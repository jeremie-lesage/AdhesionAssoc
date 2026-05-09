from sqlalchemy import Column, Integer, String, Float, Boolean, Table, ForeignKey, Date, Time
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

# Association Table for Adhesion and Activity
adhesion_activity_association = Table(
    'adhesion_activity', Base.metadata,
    Column('adhesion_id', Integer, ForeignKey('adhesions.id')),
    Column('activity_id', Integer, ForeignKey('activities.id'))
)


class Adhesion(Base):
    __tablename__ = "adhesions"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    email = Column(String, index=True)
    telephone = Column(String, nullable=True)
    nom = Column(String)
    prenom = Column(String)
    date_naissance = Column(String)
    numero_rue = Column(String)
    nom_rue = Column(String)
    code_postal = Column(String)
    ville = Column(String)
    status = Column(String, default="pending")  # pending, validated, paid
    payment_method = Column(String, nullable=True)
    adhesion_amount = Column(Float, nullable=True)

    activities = relationship("Activity", secondary=adhesion_activity_association, back_populates="adhesions")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    location = Column(String)
    resident_price = Column(Float)
    external_price = Column(Float)
    is_child_activity = Column(Boolean, default=False)
    is_adult_activity = Column(Boolean, default=False)
    max_participants = Column(Integer, default=0)
    registration_deadline = Column(Date, nullable=True)
    day_of_week = Column(Integer, nullable=True)
    start_time = Column(Time, nullable=True)
    end_time = Column(Time, nullable=True)

    adhesions = relationship("Adhesion", secondary=adhesion_activity_association, back_populates="activities")

    @property
    def current_participants(self):
        return len(self.adhesions)


class AdminUser(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
