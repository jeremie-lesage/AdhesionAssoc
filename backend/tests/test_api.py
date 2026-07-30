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


def _pay(client, auth_headers, payload=None):
    """Crée une adhésion et la mène jusqu'au statut `paid`. Renvoie son code."""
    code = client.post("/api/adhesions", json=payload or ADHESION_PAYLOAD).json()["code"]
    client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)
    client.put(
        f"/api/adhesions/{code}/pay", json={"payment_method": "cheque"}, headers=auth_headers
    )
    return code


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

    def test_a_successful_send_is_recorded(self, client, auth_headers):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]

        response = client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        assert response.json()["email_sent_at"] is not None

    def test_validation_succeeds_even_if_the_email_fails(
        self, client, auth_headers, failing_email
    ):
        """Décision produit : une panne Brevo ne doit pas bloquer la validation."""
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]

        response = client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        assert response.status_code == 200, response.text
        assert response.json()["status"] == "validated"

    def test_a_failed_send_leaves_the_adhesion_flagged(
        self, client, auth_headers, failing_email
    ):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]

        response = client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        assert response.json()["email_sent_at"] is None

    def test_the_flag_survives_a_reload(self, client, auth_headers, failing_email):
        """L'alerte du back-office doit persister : elle est lue depuis la base."""
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]
        client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        assert client.get(f"/api/adhesions/{code}").json()["email_sent_at"] is None


class TestSubmissionEmail:
    """Accusé de réception envoyé dès la soumission du formulaire.

    L'adhérent doit repartir avec son code : c'est lui qui lui permet de
    reprendre ou corriger sa demande avant validation.
    """

    def test_submission_sends_an_acknowledgement(self, client, submission_emails):
        response = client.post("/api/adhesions", json=ADHESION_PAYLOAD)

        assert len(submission_emails) == 1
        assert submission_emails[0]["email_to"] == ADHESION_PAYLOAD["email"]
        assert submission_emails[0]["body"]["code"] == response.json()["code"]

    def test_the_acknowledgement_is_recorded(self, client):
        response = client.post("/api/adhesions", json=ADHESION_PAYLOAD)

        assert response.json()["submission_email_sent_at"] is not None

    def test_submission_succeeds_even_if_the_email_fails(
        self, client, failing_submission_email
    ):
        """Un formulaire long ne doit jamais être perdu parce que Brevo est en panne."""
        response = client.post("/api/adhesions", json=ADHESION_PAYLOAD)

        assert response.status_code == 200, response.text
        assert response.json()["code"]

    def test_a_failed_acknowledgement_is_flagged(self, client, failing_submission_email):
        response = client.post("/api/adhesions", json=ADHESION_PAYLOAD)

        assert response.json()["submission_email_sent_at"] is None

    def test_the_acknowledgement_carries_a_link_to_resume_the_form(
        self, client, submission_emails
    ):
        response = client.post("/api/adhesions", json=ADHESION_PAYLOAD)

        assert response.json()["code"] in submission_emails[0]["body"]["resume_url"]


class TestResendValidationEmail:
    def _validated_code_without_email(self, client, auth_headers):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]
        client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)
        return code

    def test_resending_sends_the_email_again(
        self, client, auth_headers, failing_email, sent_emails
    ):
        code = self._validated_code_without_email(client, auth_headers)
        failing_email.restore()

        response = client.post(f"/api/adhesions/{code}/resend-email", headers=auth_headers)

        assert response.status_code == 200, response.text
        assert len(sent_emails) == 1
        assert sent_emails[0]["body"]["code"] == code

    def test_resending_records_the_send(
        self, client, auth_headers, failing_email
    ):
        code = self._validated_code_without_email(client, auth_headers)
        failing_email.restore()

        response = client.post(f"/api/adhesions/{code}/resend-email", headers=auth_headers)

        assert response.json()["email_sent_at"] is not None

    def test_a_failed_resend_reports_an_error(self, client, auth_headers, failing_email):
        """Renvoi = action explicite de l'admin : l'échec doit être une erreur HTTP."""
        code = self._validated_code_without_email(client, auth_headers)

        response = client.post(f"/api/adhesions/{code}/resend-email", headers=auth_headers)

        assert response.status_code == 502

    def test_resending_an_unknown_code_returns_404(self, client, auth_headers):
        response = client.post("/api/adhesions/INCONNU12345/resend-email", headers=auth_headers)

        assert response.status_code == 404
        # Sans cette assertion le test passerait aussi quand la route n'existe pas.
        assert response.json()["detail"] == "Adhésion introuvable"

    def test_resending_requires_a_token(self, client, auth_headers):
        code = self._validated_code_without_email(client, auth_headers)

        assert client.post(f"/api/adhesions/{code}/resend-email").status_code == 401


class TestUpdateAdhesion:
    def test_a_validated_adhesion_can_no_longer_be_edited(self, client, auth_headers):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]
        client.put(f"/api/adhesions/{code}/validate", headers=auth_headers)

        response = client.put(f"/api/adhesions/{code}", json={**ADHESION_PAYLOAD, "nom": "Martin"})

        assert response.status_code == 403

    def test_a_paid_adhesion_can_no_longer_be_edited(self, client, auth_headers):
        code = _pay(client, auth_headers)

        response = client.put(f"/api/adhesions/{code}", json={**ADHESION_PAYLOAD, "nom": "Martin"})

        assert response.status_code == 403

    def test_a_paid_adhesion_cannot_gain_activities(self, client, auth_headers, db_session):
        """`GET /api/adhesions/{code}/receipt` régénère le justificatif depuis
        l'état courant : une activité ajoutée après paiement y serait acquittée."""
        activity = _create_activity(db_session, name="Danse")
        code = _pay(client, auth_headers)

        client.put(f"/api/adhesions/{code}", json={**ADHESION_PAYLOAD, "activities": [activity.id]})

        assert client.get(f"/api/adhesions/{code}").json()["activities"] == []

    def test_an_admin_reopens_a_paid_adhesion_to_correct_it(self, client, auth_headers):
        """Chemin de correction admin : repasser en attente, puis modifier."""
        code = _pay(client, auth_headers)

        reopened = client.put(f"/api/adhesions/{code}/invalidate", headers=auth_headers)

        assert reopened.status_code == 200, reopened.text
        assert reopened.json()["status"] == "pending"
        assert reopened.json()["payment_method"] is None

        edited = client.put(f"/api/adhesions/{code}", json={**ADHESION_PAYLOAD, "nom": "Martin"})
        assert edited.status_code == 200, edited.text
        assert edited.json()["nom"] == "Martin"

    def test_reopening_requires_a_token(self, client, auth_headers):
        code = _pay(client, auth_headers)

        assert client.put(f"/api/adhesions/{code}/invalidate").status_code == 401


class TestAdminOnlyFieldsAreNotClientWritable:
    """Les champs à effet financier ne se posent que par les routes admin.

    `discount_*` a son endpoint `PUT /api/adhesions/{code}/discount` et
    `payment_method` son `PUT /api/adhesions/{code}/pay`, tous deux derrière
    `get_current_admin`. Tant qu'ils restaient dans le schéma d'entrée public,
    ce contrôle d'autorisation se contournait par la route de création ou de
    modification, qui ne demandent que le code.
    """

    def test_creation_ignores_a_client_supplied_discount(self, client):
        response = client.post(
            "/api/adhesions",
            json={**ADHESION_PAYLOAD, "discount_amount": 9999.0, "discount_reason": "Offert"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["discount_amount"] == 0
        assert response.json()["discount_reason"] is None

    def test_creation_ignores_a_client_supplied_payment_method(self, client):
        response = client.post(
            "/api/adhesions", json={**ADHESION_PAYLOAD, "payment_method": "especes"}
        )

        assert response.status_code == 200, response.text
        assert response.json()["payment_method"] is None

    def test_update_cannot_overwrite_a_discount_granted_by_an_admin(self, client, auth_headers):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]
        client.put(
            f"/api/adhesions/{code}/discount",
            json={"discount_amount": 5.0, "discount_reason": "Bénévole"},
            headers=auth_headers,
        )

        response = client.put(
            f"/api/adhesions/{code}",
            json={**ADHESION_PAYLOAD, "discount_amount": 9999.0, "discount_reason": "Offert"},
        )

        assert response.status_code == 200, response.text
        assert response.json()["discount_amount"] == 5.0
        assert response.json()["discount_reason"] == "Bénévole"

    def test_update_cannot_mark_an_adhesion_as_paid(self, client):
        code = client.post("/api/adhesions", json=ADHESION_PAYLOAD).json()["code"]

        response = client.put(
            f"/api/adhesions/{code}", json={**ADHESION_PAYLOAD, "payment_method": "especes"}
        )

        assert response.status_code == 200, response.text
        assert response.json()["payment_method"] is None

    def test_a_legitimate_payload_still_goes_through(self, client):
        """Le formulaire renvoie tout son état, dont `code` et `status` : le
        schéma restreint doit ignorer l'inconnu, pas rejeter la soumission."""
        response = client.post(
            "/api/adhesions", json={**ADHESION_PAYLOAD, "code": "PEUIMPORTE00", "status": "paid"}
        )

        assert response.status_code == 200, response.text
        assert response.json()["code"] != "PEUIMPORTE00"
        assert response.json()["status"] == "pending"


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
