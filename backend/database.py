import os
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/foyer_rural_db")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Adhesion(Base):
    __tablename__ = "adhesions"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, nullable=False)
    email = Column(String, nullable=False)
    nom = Column(String)
    prenom = Column(String)
    date_naissance = Column(String)
    numero_rue = Column(String)
    nom_rue = Column(String)
    code_postal = Column(String)
    ville = Column(String)
    adhesion_amount = Column(Float)
    payment_method = Column(String)
    status = Column(String, default='pending')

    adhesion_activities_link = relationship("AdhesionActivity", back_populates="adhesion")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, default='')
    location = Column(String, default='')
    resident_price = Column(Float, default=0.0)
    external_price = Column(Float, default=0.0)
    is_child_activity = Column(Boolean, default=False)
    is_adult_activity = Column(Boolean, default=False)
    max_participants = Column(Integer, default=0)

    adhesions_link = relationship("AdhesionActivity", back_populates="activity")

class AdhesionActivity(Base):
    __tablename__ = "adhesion_activities"
    adhesion_id = Column(Integer, ForeignKey("adhesions.id"), primary_key=True)
    activity_id = Column(Integer, ForeignKey("activities.id"), primary_key=True)

    adhesion = relationship("Adhesion", back_populates="adhesion_activities_link")
    activity = relationship("Activity", back_populates="adhesions_link")

class Admin(Base):
    __tablename__ = "admins"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    print("Creating/updating database tables...")
    Base.metadata.create_all(engine)

    db = SessionLocal()
    default_activities_data = [
        {'name': 'danse', 'description': 'Cours de danse pour tous les âges', 'location': 'Salle Polyvalente', 'resident_price': 100.0, 'external_price': 120.0, 'is_child_activity': True, 'is_adult_activity': True},
        {'name': 'gym', 'description': 'Séances de gymnastique douce', 'location': 'Gymnase', 'resident_price': 80.0, 'external_price': 100.0, 'is_child_activity': False, 'is_adult_activity': True},
        {'name': 'pilate', 'description': 'Cours de Pilate pour renforcer le corps', 'location': 'Salle de Fitness', 'resident_price': 90.0, 'external_price': 110.0, 'is_child_activity': False, 'is_adult_activity': True}
    ]

    for activity_data in default_activities_data:
        existing_activity = db.query(Activity).filter_by(name=activity_data['name']).first()
        if not existing_activity:
            activity = Activity(**activity_data)
            db.add(activity)
    db.commit()
    db.close()

if __name__ == "__main__":
    create_tables()