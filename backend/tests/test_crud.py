import pytest
import sys
import os
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Base, Activity, Adhesion
from schemas import AdhesionCreate
import crud

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)

def test_create_adhesion_with_activities(db_session):
    # 1. Create some activities to link to
    activity1 = Activity(name="Yoga", description="Cours de Yoga", resident_price=100, external_price=120)
    activity2 = Activity(name="Danse", description="Cours de Danse", resident_price=110, external_price=130)
    db_session.add_all([activity1, activity2])
    db_session.commit()
    db_session.refresh(activity1)
    db_session.refresh(activity2)

    # 2. Prepare the adhesion data with activity IDs
    adhesion_data = AdhesionCreate(
        email="test.adhesion@example.com",
        nom="Test",
        prenom="Adherent",
        date_naissance="2000-01-01",
        ville="Testville",
        activities=[activity1.id, activity2.id]
    )

    # 3. Call the function to be tested
    created_adhesion_pydantic = crud.create_adhesion(db=db_session, adhesion=adhesion_data)
    
    # 4. Verify the result from the database
    # Use the Pydantic model's ID to fetch the record
    db_adhesion = db_session.query(Adhesion).filter(Adhesion.id == created_adhesion_pydantic.id).one_or_none()

    assert db_adhesion is not None
    assert db_adhesion.email == "test.adhesion@example.com"
    
    # THE CRITICAL TEST: Check if the activities were associated
    assert len(db_adhesion.activities) == 2
    
    activity_names_in_db = sorted([act.name for act in db_adhesion.activities])
    assert activity_names_in_db == ["Danse", "Yoga"]

def test_update_adhesion_with_activities(db_session):
    # 1. Create an initial adhesion with one activity
    activity1 = Activity(name="Yoga", description="Cours de Yoga")
    activity2 = Activity(name="Danse", description="Cours de Danse")
    activity3 = Activity(name="Musique", description="Cours de Musique")
    db_session.add_all([activity1, activity2, activity3])
    db_session.commit()

    initial_adhesion_data = AdhesionCreate(
        email="update.test@example.com",
        nom="Update",
        prenom="Test",
        activities=[activity1.id]
    )
    created_adhesion = crud.create_adhesion(db=db_session, adhesion=initial_adhesion_data)
    
    # 2. Prepare the update data, changing the activities
    update_adhesion_data = AdhesionCreate(
        email="update.test@example.com", # email is the same
        nom="UpdatedNom", # name is changed
        activities=[activity2.id, activity3.id] # activities are changed
    )

    # 3. Call the update function
    updated_adhesion_pydantic = crud.update_adhesion(db=db_session, code=created_adhesion.code, adhesion=update_adhesion_data)

    # 4. Verify the result from the database
    db_adhesion = db_session.query(Adhesion).filter(Adhesion.id == updated_adhesion_pydantic.id).one()

    assert db_adhesion is not None
    assert db_adhesion.nom == "UpdatedNom"
    assert len(db_adhesion.activities) == 2
    
    activity_names_in_db = sorted([act.name for act in db_adhesion.activities])
    assert activity_names_in_db == ["Danse", "Musique"]

def test_update_adhesion_without_activities_preserves_them(db_session):
    """Updating fields without sending activities should not clear existing ones."""
    activity1 = Activity(name="Yoga", description="Cours de Yoga")
    activity2 = Activity(name="Danse", description="Cours de Danse")
    db_session.add_all([activity1, activity2])
    db_session.commit()

    initial = AdhesionCreate(
        email="preserve@example.com",
        nom="Original",
        prenom="Test",
        activities=[activity1.id, activity2.id]
    )
    created = crud.create_adhesion(db=db_session, adhesion=initial)

    update_without_activities = AdhesionCreate.model_construct(
        email="preserve@example.com",
        nom="Modified",
    )

    updated = crud.update_adhesion(db=db_session, code=created.code, adhesion=update_without_activities)

    db_adhesion = db_session.query(Adhesion).filter(Adhesion.id == updated.id).one()
    assert db_adhesion.nom == "Modified"
    assert len(db_adhesion.activities) == 2, "Activities should be preserved when not included in update"
    activity_names = sorted([a.name for a in db_adhesion.activities])
    assert activity_names == ["Danse", "Yoga"]
