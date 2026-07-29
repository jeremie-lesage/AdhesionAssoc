"""Tests des endpoints HTTP.

Ces tests passent par l'application FastAPI complète (validation Pydantic,
dépendances, auth JWT, rate limiting) contre la base SQLite des fixtures.
`crud` est testé séparément dans test_crud.py.
"""

from models import Activity

# Fixtures : voir tests/conftest.py (client, auth_headers, db_session, sent_emails).

ADHESION_PAYLOAD = {
    "email": "jean.dupont@example.com",
    "nom": "Dupont",
    "prenom": "Jean",
    "date_naissance": "01/01/1990",
    "numero_rue": "12",
    "nom_rue": "rue des Lilas",
    "code_postal": "21110",
    "ville": "Fauverney",
    "adhesion_amount": 15.0,
    "activities": [],
}


def _create_activity(db_session, name="Yoga", resident_price=100.0, external_price=120.0,
                     max_participants=0):
    activity = Activity(
        name=name,
        description=f"Cours de {name}",
        resident_price=resident_price,
        external_price=external_price,
        max_participants=max_participants,
    )
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    return activity


class TestConfig:
    def test_exposes_public_settings_only(self, client):
        response = client.get("/api/config")

        assert response.status_code == 200
        body = response.json()
        assert set(body) == {
            "iban", "bic", "bank", "postal_code_prefix", "adult_age_threshold",
        }


class TestToken:
    def test_valid_credentials_return_a_bearer_token(self, client, admin_user):
        username, password = admin_user

        response = client.post("/api/token", data={"username": username, "password": password})

        assert response.status_code == 200
        assert response.json()["token_type"] == "bearer"
        assert response.json()["access_token"]

    def test_wrong_password_is_rejected(self, client, admin_user):
        username, _ = admin_user

        response = client.post("/api/token", data={"username": username, "password": "nope"})

        assert response.status_code == 401

    def test_unknown_user_is_rejected(self, client, admin_user):
        response = client.post(
            "/api/token", data={"username": "inconnu", "password": "peu importe"}
        )

        assert response.status_code == 401


class TestAdhesionsAuthorization:
    def test_listing_adhesions_requires_a_token(self, client):
        assert client.get("/api/adhesions").status_code == 401

    def test_listing_adhesions_rejects_a_forged_token(self, client):
        response = client.get(
            "/api/adhesions", headers={"Authorization": "Bearer pas-un-vrai-jwt"}
        )

        assert response.status_code == 401

    def test_listing_adhesions_succeeds_with_a_token(self, client, auth_headers):
        response = client.get("/api/adhesions", headers=auth_headers)

        assert response.status_code == 200
        assert response.json() == []


class TestCreateAdhesion:
    def test_creates_a_pending_adhesion_with_a_generated_code(self, client):
        response = client.post("/api/adhesions", json=ADHESION_PAYLOAD)

        assert response.status_code == 200, response.text
        body = response.json()
        assert body["status"] == "pending"
        assert len(body["code"]) == 12
        assert body["email"] == ADHESION_PAYLOAD["email"]

    def test_rejects_an_invalid_email(self, client):
        response = client.post("/api/adhesions", json={**ADHESION_PAYLOAD, "email": "pas-un-email"})

        assert response.status_code == 422

    def test_rejects_a_full_activity_with_400(self, client, db_session):
        activity = _create_activity(db_session, max_participants=1)
        first = client.post(
            "/api/adhesions", json={**ADHESION_PAYLOAD, "activities": [activity.id]}
        )
        assert first.status_code == 200, first.text

        second = client.post(
            "/api/adhesions",
            json={**ADHESION_PAYLOAD, "email": "autre@example.com", "activities": [activity.id]},
        )

        assert second.status_code == 400
        assert "maximum number of participants" in second.json()["detail"]

    def test_is_rate_limited_after_five_requests(self, client):
        for i in range(5):
            response = client.post(
                "/api/adhesions", json={**ADHESION_PAYLOAD, "email": f"adherent{i}@example.com"}
            )
            assert response.status_code == 200, response.text

        blocked = client.post(
            "/api/adhesions", json={**ADHESION_PAYLOAD, "email": "sixieme@example.com"}
        )

        assert blocked.status_code == 429


class TestReadAdhesion:
    def test_reads_an_adhesion_by_code(self, client):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]

        response = client.get(f"/api/adhesions/{code}")

        assert response.status_code == 200
        assert response.json()["code"] == code

    def test_unknown_code_returns_404(self, client):
        assert client.get("/api/adhesions/INCONNU12345").status_code == 404


class TestValidateAdhesion:
    def test_validation_flips_the_status_and_sends_an_email(
        self, client, auth_headers, sent_emails
    ):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]

        response = client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        assert response.status_code == 200, response.text
        assert response.json()["status"] == "validated"
        assert len(sent_emails) == 1
        assert sent_emails[0]["email_to"] == ADHESION_PAYLOAD["email"]
        assert sent_emails[0]["body"]["code"] == code

    def test_validation_email_totals_the_resident_price(
        self, client, auth_headers, db_session, sent_emails
    ):
        activity = _create_activity(db_session, resident_price=100.0, external_price=120.0)
        code = client.post(
            "/api/adhesions", json={**ADHESION_PAYLOAD, "activities": [activity.id]}
        ).json()["code"]

        client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        # Fauverney → tarif résident, plus les 15 € d'adhésion.
        assert sent_emails[0]["body"]["total_cost"] == 115.0

    def test_validation_email_totals_the_external_price(
        self, client, auth_headers, db_session, sent_emails
    ):
        activity = _create_activity(db_session, resident_price=100.0, external_price=120.0)
        code = client.post(
            "/api/adhesions",
            json={**ADHESION_PAYLOAD, "ville": "Dijon", "activities": [activity.id]},
        ).json()["code"]

        client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        assert sent_emails[0]["body"]["total_cost"] == 135.0

    def test_validating_twice_returns_404(self, client, auth_headers):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]
        assert client.put(f"/api/adhesions/{code}/validate", headers=auth_headers).status_code == 200

        second = client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        assert second.status_code == 404

    def test_validation_requires_a_token(self, client):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]

        assert client.put(f"/api/adhesions/{code}/validate").status_code == 401

    def test_no_email_is_sent_without_validation(self, client, sent_emails):
        client.post("/api/adhesions", json=ADHESION_PAYLOAD)

        assert sent_emails == []


class TestUpdateAdhesion:
    def test_a_validated_adhesion_can_no_longer_be_edited(self, client, auth_headers):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]
        client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        response = client.put(f"/api/adhesions/{code}", json={**ADHESION_PAYLOAD, "nom": "Martin"})

        assert response.status_code == 403


class TestActivities:
    def test_listing_activities_is_public(self, client, db_session):
        _create_activity(db_session, name="Danse")

        response = client.get("/api/activities")

        assert response.status_code == 200
        assert [a["name"] for a in response.json()] == ["Danse"]

    def test_creating_an_activity_requires_a_token(self, client):
        response = client.post("/api/activities", json={"name": "Judo", "description": ""})

        assert response.status_code == 401

    def test_creating_an_activity_as_admin_returns_201(self, client, auth_headers):
        response = client.post(
            "/api/activities",
            json={
                "name": "Judo",
                "description": "Cours de judo",
                "resident_price": 90.0,
                "external_price": 110.0,
                "max_participants": 20,
            },
            headers=auth_headers,
        )

        assert response.status_code == 201, response.text
        assert response.json()["name"] == "Judo"


class TestDashboardStats:
    def test_counts_residents_and_statuses(self, client, auth_headers):
        client.post("/api/adhesions", json=ADHESION_PAYLOAD)
        client.post(
            "/api/adhesions",
            json={**ADHESION_PAYLOAD, "email": "exterieur@example.com", "ville": "Dijon"},
        )

        response = client.get("/api/admin/stats", headers=auth_headers)

        assert response.status_code == 200, response.text
        stats = response.json()
        assert stats["total_adhesions"] == 2
        assert stats["pending"] == 2
        assert stats["validated"] == 0
        assert stats["residents"] == 1
        assert stats["external"] == 1
        assert stats["total_contacts"] == 2
