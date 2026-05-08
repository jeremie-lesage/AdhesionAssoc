import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from models import Base, Adhesion, Activity, adhesion_activity_association

TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="module")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def test_session(test_engine):
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def test_create_tables(test_engine):
    table_names = inspect(test_engine).get_table_names()
    assert Adhesion.__tablename__ in table_names
    assert Activity.__tablename__ in table_names
    assert adhesion_activity_association.name in table_names


def test_create_activity(test_session):
    activity = Activity(name="Test Activity", description="A test activity", max_participants=10)
    test_session.add(activity)
    test_session.commit()
    test_session.refresh(activity)
    assert activity.id is not None
    assert activity.name == "Test Activity"


def test_create_adhesion(test_session):
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
    test_session.add(adhesion)
    test_session.commit()
    test_session.refresh(adhesion)
    assert adhesion.id is not None
    assert adhesion.email == "test@example.com"


def test_adhesion_activity_link(test_session):
    activity = Activity(name="Linked Activity", description="", max_participants=10)
    test_session.add(activity)
    test_session.commit()
    test_session.refresh(activity)

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
    test_session.add(adhesion)
    test_session.commit()
    test_session.refresh(adhesion)

    adhesion.activities.append(activity)
    test_session.commit()

    assert activity in adhesion.activities
