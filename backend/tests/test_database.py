from sqlalchemy import inspect

from models import Activity, Adhesion, adhesion_activity_association

# Les fixtures `db_engine` / `db_session` viennent de tests/conftest.py.


def test_create_tables(db_engine):
    table_names = inspect(db_engine).get_table_names()
    assert Adhesion.__tablename__ in table_names
    assert Activity.__tablename__ in table_names
    assert adhesion_activity_association.name in table_names


def test_create_activity(db_session):
    activity = Activity(name="Test Activity", description="A test activity", max_participants=10)
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)
    assert activity.id is not None
    assert activity.name == "Test Activity"


def test_create_adhesion(db_session):
    adhesion = Adhesion(
        code="TESTCODE123",
        email="test@example.com",
        nom="Doe",
        prenom="John",
        date_naissance="01/01/2000",
        numero_rue="1",
        nom_rue="Test Street",
        code_postal="12345",
        ville="Testville",
        adhesion_amount=10.0,
        payment_method="Cash"
    )
    db_session.add(adhesion)
    db_session.commit()
    db_session.refresh(adhesion)
    assert adhesion.id is not None
    assert adhesion.email == "test@example.com"


def test_adhesion_activity_link(db_session):
    activity = Activity(name="Linked Activity", description="", max_participants=10)
    db_session.add(activity)
    db_session.commit()
    db_session.refresh(activity)

    adhesion = Adhesion(
        code="LINKCODE456",
        email="link@example.com",
        nom="Smith",
        prenom="Jane",
        date_naissance="01/01/1990",
        numero_rue="2",
        nom_rue="Link Road",
        code_postal="54321",
        ville="Linktown",
        adhesion_amount=20.0,
        payment_method="Card"
    )
    db_session.add(adhesion)
    db_session.commit()
    db_session.refresh(adhesion)

    adhesion.activities.append(activity)
    db_session.commit()

    assert activity in adhesion.activities
