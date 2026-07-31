import random
import string
from datetime import date, timedelta

import pytest

import crud
from models import Activity, Adhesion
from schemas import ActivityCreate, AdhesionInput, AdminUserCreate

# La fixture `db_session` vient de tests/conftest.py.


def _make_activity(db_session, name="Yoga", resident_price=100, external_price=120, max_participants=0):
    a = Activity(name=name, description=f"Cours de {name}", resident_price=resident_price,
                 external_price=external_price, max_participants=max_participants)
    db_session.add(a)
    db_session.commit()
    db_session.refresh(a)
    return a


def _make_adhesion(db_session, email="test@example.com", nom="Dupont", prenom="Jean",
                   ville="Fauverney", activities=None, date_naissance=None):
    data = AdhesionInput(email=email, nom=nom, prenom=prenom, ville=ville,
                          date_naissance=date_naissance, activities=activities or [])
    return crud.create_adhesion(db=db_session, adhesion=data)


def _birthdate_for_age(age: int) -> str:
    """Date de naissance donnant `age` révolus, au format attendu par la base.

    Le calcul de `get_dashboard_stats` divise un nombre de jours par 365 : on
    prend une marge de quelques jours pour rester du bon côté du seuil quelles
    que soient les années bissextiles traversées.
    """
    return (date.today() - timedelta(days=age * 365 + 5)).strftime("%Y-%m-%d")


# ─── Génération des codes d'accès ────────────────────────────────


class TestGenerateRandomCode:
    """Le code est le seul authentifiant de l'adhérent.

    Il ouvre `GET /api/adhesions/{code}` (données personnelles complètes),
    `PUT /api/adhesions/{code}` et le reçu. Il doit donc venir d'une source
    cryptographique, pas du PRNG généraliste du processus.
    """

    def test_the_code_does_not_depend_on_the_global_prng_state(self):
        """`random.seed(n)` ne doit pas rendre les codes rejouables.

        Le Mersenne Twister est réversible : à partir d'assez de sorties
        observées — et `POST /api/adhesions` renvoie le code à son auteur — son
        état interne se reconstitue, livrant les codes passés comme à venir.
        """
        state = random.getstate()
        try:
            random.seed(0)
            first = crud.generate_random_code()
            random.seed(0)
            second = crud.generate_random_code()
        finally:
            random.setstate(state)

        assert first != second

    def test_uses_the_expected_length_and_alphabet(self):
        code = crud.generate_random_code()

        assert len(code) == 12
        assert set(code) <= set(string.ascii_uppercase + string.digits)


# ─── Adhesion CRUD ───────────────────────────────────────────────


class TestCreateAdhesion:
    def test_create_with_activities(self, db_session):
        a1 = _make_activity(db_session, "Yoga")
        a2 = _make_activity(db_session, "Danse")

        result = _make_adhesion(db_session, activities=[a1.id, a2.id])

        assert result.email == "test@example.com"
        assert result.code is not None
        assert len(result.code) == 12
        assert result.status == "pending"
        assert len(result.activities) == 2

    def test_create_without_activities(self, db_session):
        result = _make_adhesion(db_session)
        assert result.activities == []
        assert result.status == "pending"

    def test_create_generates_unique_codes(self, db_session):
        a1 = _make_adhesion(db_session, email="a@example.com")
        a2 = _make_adhesion(db_session, email="b@example.com")
        assert a1.code != a2.code

    def test_create_rejects_full_activity(self, db_session):
        a = _make_activity(db_session, "Yoga", max_participants=1)
        _make_adhesion(db_session, email="first@example.com", activities=[a.id])

        with pytest.raises(ValueError, match="maximum number of participants"):
            _make_adhesion(db_session, email="second@example.com", activities=[a.id])


class TestGetAdhesion:
    def test_get_by_code(self, db_session):
        created = _make_adhesion(db_session)
        result = crud.get_adhesion_by_code(db_session, created.code)
        assert result is not None
        assert result.id == created.id

    def test_get_by_code_not_found(self, db_session):
        result = crud.get_adhesion_by_code(db_session, "INEXISTANT")
        assert result is None

    def test_get_all(self, db_session):
        _make_adhesion(db_session, email="a@example.com")
        _make_adhesion(db_session, email="b@example.com")
        result = crud.get_adhesions(db_session)
        assert len(result) == 2


class TestUpdateAdhesion:
    def test_update_fields_and_activities(self, db_session):
        a1 = _make_activity(db_session, "Yoga")
        a2 = _make_activity(db_session, "Danse")
        created = _make_adhesion(db_session, activities=[a1.id])

        update = AdhesionInput(email="test@example.com", nom="Modifié", activities=[a2.id])
        result = crud.update_adhesion(db_session, created.code, update)

        assert result.nom == "Modifié"
        assert len(result.activities) == 1
        assert result.activities[0].name == "Danse"

    def test_update_without_activities_preserves_them(self, db_session):
        a1 = _make_activity(db_session, "Yoga")
        a2 = _make_activity(db_session, "Danse")
        created = _make_adhesion(db_session, activities=[a1.id, a2.id])

        update = AdhesionInput.model_construct(email="test@example.com", nom="Modifié")
        result = crud.update_adhesion(db_session, created.code, update)

        assert result.nom == "Modifié"
        assert len(result.activities) == 2

    def test_update_not_found(self, db_session):
        update = AdhesionInput(email="x@example.com")
        result = crud.update_adhesion(db_session, "INEXISTANT", update)
        assert result is None

    def test_update_validated_adhesion_raises(self, db_session):
        created = _make_adhesion(db_session)
        db_adhesion = db_session.query(Adhesion).filter(Adhesion.id == created.id).one()
        db_adhesion.status = "validated"
        db_session.commit()

        update = AdhesionInput(email="test@example.com", nom="Nouveau")
        with pytest.raises(ValueError, match="Cannot update a validated adhesion"):
            crud.update_adhesion(db_session, created.code, update)

    def test_update_paid_adhesion_raises(self, db_session):
        """Le frontend bloque déjà `paid` (LoadForm.vue) : le serveur doit aussi."""
        created = _make_adhesion(db_session)
        db_adhesion = db_session.query(Adhesion).filter(Adhesion.id == created.id).one()
        db_adhesion.status = "paid"
        db_session.commit()

        update = AdhesionInput(email="test@example.com", nom="Nouveau")
        with pytest.raises(ValueError, match="Cannot update a paid adhesion"):
            crud.update_adhesion(db_session, created.code, update)

    def test_update_rejects_a_full_activity(self, db_session):
        a = _make_activity(db_session, "Yoga", max_participants=1)
        _make_adhesion(db_session, email="first@example.com", activities=[a.id])
        created = _make_adhesion(db_session, email="second@example.com")

        update = AdhesionInput(email="second@example.com", activities=[a.id])
        with pytest.raises(ValueError, match="maximum number of participants"):
            crud.update_adhesion(db_session, created.code, update)

    def test_update_keeps_an_activity_the_adherent_already_joined(self, db_session):
        """Le quota ne compte que les *autres* inscrits.

        Sans cela, un adhérent seul sur une activité complète ne pourrait plus
        corriger son dossier : sa propre inscription saturerait le quota.
        """
        a = _make_activity(db_session, "Yoga", max_participants=1)
        created = _make_adhesion(db_session, activities=[a.id])

        update = AdhesionInput(email="test@example.com", nom="Modifié", activities=[a.id])
        result = crud.update_adhesion(db_session, created.code, update)

        assert result.nom == "Modifié"
        assert [act.name for act in result.activities] == ["Yoga"]


class TestInvalidateAdhesion:
    """`invalidate` est le seul retour en arrière du cycle de vie.

    Puisque la modification est désormais réservée au statut `pending`, c'est par
    là que passe un admin qui veut corriger un dossier déjà validé ou encaissé.
    """

    def test_invalidate_a_validated_adhesion(self, db_session):
        created = _make_adhesion(db_session)
        db_session.query(Adhesion).filter(Adhesion.id == created.id).one().status = "validated"
        db_session.commit()

        result = crud.invalidate_adhesion(db_session, created.code)

        assert result.status == "pending"

    def test_invalidate_a_paid_adhesion_clears_the_payment(self, db_session):
        """Sans effacer `payment_method`, l'adhésion resterait « en attente,
        payée par chèque » — un état que le back-office afficherait tel quel."""
        created = _make_adhesion(db_session)
        crud.update_adhesion_payment(db_session, created.code, "cheque")

        result = crud.invalidate_adhesion(db_session, created.code)

        assert result.status == "pending"
        assert result.payment_method is None

    def test_invalidate_unknown_code_returns_none(self, db_session):
        assert crud.invalidate_adhesion(db_session, "INEXISTANT") is None


class TestUpdatePayment:
    def test_mark_as_paid(self, db_session):
        created = _make_adhesion(db_session)
        result = crud.update_adhesion_payment(db_session, created.code, "cheque")

        assert result.status == "paid"
        assert result.payment_method == "cheque"

    def test_payment_not_found(self, db_session):
        result = crud.update_adhesion_payment(db_session, "INEXISTANT", "cheque")
        assert result is None


class TestDeleteAdhesion:
    def test_delete_existing(self, db_session):
        created = _make_adhesion(db_session)
        assert crud.delete_adhesion(db_session, created.code) is True
        assert crud.get_adhesion_by_code(db_session, created.code) is None

    def test_delete_not_found(self, db_session):
        assert crud.delete_adhesion(db_session, "INEXISTANT") is False


# ─── Activity CRUD ───────────────────────────────────────────────


class TestActivityCrud:
    def test_create_activity(self, db_session):
        data = ActivityCreate(name="Peinture", description="Atelier peinture",
                              resident_price=50, external_price=70)
        result = crud.create_activity(db_session, data)
        assert result.id is not None
        assert result.name == "Peinture"

    def test_get_activities(self, db_session):
        _make_activity(db_session, "Yoga")
        _make_activity(db_session, "Danse")
        result = crud.get_activities(db_session)
        assert len(result) == 2

    def test_update_activity(self, db_session):
        a = _make_activity(db_session, "Yoga", resident_price=100)
        update = ActivityCreate(name="Yoga avancé", resident_price=150)
        result = crud.update_activity(db_session, a.id, update)
        assert result.name == "Yoga avancé"
        assert result.resident_price == 150

    def test_update_activity_not_found(self, db_session):
        update = ActivityCreate(name="X")
        result = crud.update_activity(db_session, 999, update)
        assert result is None

    def test_delete_activity(self, db_session):
        a = _make_activity(db_session, "Yoga")
        assert crud.delete_activity(db_session, a.id) is True
        assert crud.delete_activity(db_session, a.id) is False

    def test_get_adherents_by_activity(self, db_session):
        a = _make_activity(db_session, "Yoga")
        _make_adhesion(db_session, email="a@example.com", activities=[a.id])
        _make_adhesion(db_session, email="b@example.com", activities=[a.id])

        result = crud.get_adherents_by_activity(db_session, a.id)
        assert len(result) == 2

    def test_get_adherents_by_activity_not_found(self, db_session):
        with pytest.raises(ValueError, match="Activity not found"):
            crud.get_adherents_by_activity(db_session, 999)


# ─── Admin CRUD ──────────────────────────────────────────────────


class TestAdminCrud:
    def test_create_and_get_admin(self, db_session):
        admin = AdminUserCreate(username="admin", password="hashed_pw")
        result = crud.create_admin(db_session, admin)
        assert result.username == "admin"
        assert result.id is not None

    def test_get_admin_by_username(self, db_session):
        crud.create_admin(db_session, AdminUserCreate(username="admin", password="pw"))
        result = crud.get_admin_by_username(db_session, "admin")
        assert result is not None
        assert result.username == "admin"

    def test_get_admin_by_username_not_found(self, db_session):
        result = crud.get_admin_by_username(db_session, "inexistant")
        assert result is None

    def test_get_admins(self, db_session):
        crud.create_admin(db_session, AdminUserCreate(username="admin1", password="pw"))
        crud.create_admin(db_session, AdminUserCreate(username="admin2", password="pw"))
        result = crud.get_admins(db_session)
        assert len(result) == 2

    def test_update_admin(self, db_session):
        created = crud.create_admin(db_session, AdminUserCreate(username="old", password="pw"))
        update = AdminUserCreate(username="new", password="new_pw")
        result = crud.update_admin(db_session, created.id, update)
        assert result.username == "new"

    def test_update_admin_not_found(self, db_session):
        update = AdminUserCreate(username="x", password="pw")
        result = crud.update_admin(db_session, 999, update)
        assert result is None

    def test_delete_admin(self, db_session):
        created = crud.create_admin(db_session, AdminUserCreate(username="admin", password="pw"))
        assert crud.delete_admin(db_session, created.id) is True
        assert crud.delete_admin(db_session, created.id) is False


# ─── Contacts & Family ──────────────────────────────────────────


class TestContactsAndFamily:
    def test_contacts_status_pending(self, db_session):
        _make_adhesion(db_session, email="a@example.com")
        result = crud.get_contacts_with_status(db_session)
        assert len(result) == 1
        assert result[0].status == "pending"

    def test_contacts_status_paid(self, db_session):
        created = _make_adhesion(db_session, email="a@example.com")
        crud.update_adhesion_payment(db_session, created.code, "cb")

        result = crud.get_contacts_with_status(db_session)
        assert result[0].status == "payé"

    def test_contacts_status_mixed(self, db_session):
        a1 = _make_adhesion(db_session, email="famille@example.com", nom="Parent")
        _make_adhesion(db_session, email="famille@example.com", nom="Enfant")
        crud.update_adhesion_payment(db_session, a1.code, "cb")

        result = crud.get_contacts_with_status(db_session)
        assert len(result) == 1
        assert result[0].status == "pending"

    def test_family_details(self, db_session):
        a = _make_activity(db_session, "Yoga", resident_price=100, external_price=120)
        _make_adhesion(db_session, email="famille@example.com", nom="Parent",
                       ville="Fauverney", activities=[a.id])
        _make_adhesion(db_session, email="famille@example.com", nom="Enfant",
                       ville="Fauverney", activities=[a.id])

        result = crud.get_family_details_by_email(db_session, "famille@example.com")
        assert result is not None
        assert len(result.adherents) == 2
        assert result.total_due == 200  # 2 x 100 (résident)

    def test_family_details_external_pricing(self, db_session):
        a = _make_activity(db_session, "Yoga", resident_price=100, external_price=150)
        _make_adhesion(db_session, email="ext@example.com", nom="Externe",
                       ville="Dijon", activities=[a.id])

        result = crud.get_family_details_by_email(db_session, "ext@example.com")
        assert result.total_due == 150

    def test_family_details_not_found(self, db_session):
        result = crud.get_family_details_by_email(db_session, "inexistant@example.com")
        assert result is None

    def test_family_details_with_adhesion_amount(self, db_session):
        a = _make_activity(db_session, "Yoga", resident_price=100, external_price=120)
        data = AdhesionInput(email="cotis@example.com", nom="Test", ville="Fauverney",
                              adhesion_amount=15, activities=[a.id])
        crud.create_adhesion(db_session, data)

        result = crud.get_family_details_by_email(db_session, "cotis@example.com")
        assert result.total_due == 115  # 15 (cotisation) + 100 (activité résident)


# ─── Dashboard ───────────────────────────────────────────────────


class TestDashboardAgeSplit:
    """Répartition enfants / adultes, pilotée par settings.ADULT_AGE_THRESHOLD."""

    def test_split_on_default_threshold(self, db_session):
        _make_adhesion(db_session, email="petit@example.com",
                       date_naissance=_birthdate_for_age(10))
        _make_adhesion(db_session, email="grand@example.com",
                       date_naissance=_birthdate_for_age(20))

        stats = crud.get_dashboard_stats(db_session)

        assert stats.children == 1
        assert stats.adults == 1

    def test_threshold_is_configurable(self, db_session, monkeypatch):
        _make_adhesion(db_session, email="ado@example.com",
                       date_naissance=_birthdate_for_age(17))

        # 17 ans : adulte avec le seuil par défaut (16)…
        assert crud.get_dashboard_stats(db_session).adults == 1

        # …enfant si l'association relève le seuil à 18.
        monkeypatch.setattr(crud.settings, "ADULT_AGE_THRESHOLD", 18)
        stats = crud.get_dashboard_stats(db_session)

        assert stats.children == 1
        assert stats.adults == 0

    def test_missing_or_invalid_birthdate_counts_as_adult(self, db_session):
        _make_adhesion(db_session, email="vide@example.com", date_naissance=None)
        _make_adhesion(db_session, email="casse@example.com", date_naissance="pas-une-date")

        stats = crud.get_dashboard_stats(db_session)

        assert stats.children == 0
        assert stats.adults == 2
