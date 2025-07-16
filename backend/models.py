from sqlalchemy import Column, Integer, String, Float, Boolean, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

# Pydantic model for admin login
from pydantic import BaseModel, EmailStr
from typing import List, Optional

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

    adhesions = relationship("Adhesion", secondary=adhesion_activity_association, back_populates="activities")

    @property
    def current_participants(self):
        return len(self.adhesions)


class AdminUser(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)


class AdminLogin(BaseModel):
    """
    Represents the data structure for an administrator's login credentials.

    This class is used to validate and manage the login credentials for an
    administrator. It ensures the required information, such as the username and
    password, is provided and adheres to any specified validation rules.

    :ivar username: The username of the administrator attempting to log in.
    :type username: str
    :ivar password: The password associated with the administrator's account.
    :type password: str
    """
    username: str
    password: str


# Pydantic models for Adhesion
class AdhesionBase(BaseModel):
    """
    Represents the base model for an adhesion record.

    This class serves as a base for defining the structure of an adhesion record.
    It includes details such as address, contact information, and other related
    attributes necessary for storing and managing adhesion data.

    :ivar email: The email address of the individual.
    :type email: EmailStr
    :ivar nom: The last name of the individual.
    :type nom: Optional[str]
    :ivar prenom: The first name of the individual.
    :type prenom: Optional[str]
    :ivar date_naissance: The birthdate of the individual in string format.
    :type date_naissance: Optional[str]
    :ivar numero_rue: The street number of the individual's address.
    :type numero_rue: Optional[str]
    :ivar nom_rue: The street name of the individual's address.
    :type nom_rue: Optional[str]
    :ivar code_postal: The postal code of the individual's address.
    :type code_postal: Optional[str]
    :ivar ville: The city of the individual's address.
    :type ville: Optional[str]
    :ivar adhesion_amount: The amount associated with the adhesion.
    :type adhesion_amount: Optional[float]
    :ivar payment_method: The method of payment for the adhesion.
    :type payment_method: Optional[str]
    """
    email: EmailStr
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[str] = None
    numero_rue: Optional[str] = None
    nom_rue: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    adhesion_amount: Optional[float] = None
    payment_method: Optional[str] = None


class AdhesionCreate(AdhesionBase):
    activities: Optional[List[int]] = []
    pass


class AdhesionSchema(AdhesionBase):
    id: int
    code: str
    status: str
    activities: List['ActivitySchema'] = []

    class Config:
        from_attributes = True


class AdhesionPaymentUpdate(BaseModel):
    payment_method: str


# Pydantic models for Activity
class ActivityBase(BaseModel):
    """
    Represents a base model for an activity that contains details about the activity's name,
    description, pricing, location, participants, and eligibility.

    This class serves as a foundational model for activity-related data. It allows you to
    define and manipulate attributes of an activity, such as its name, description, location,
    pricing for residents and non-residents, participant limits, and whether the activity
    is tailored for children or adults.

    :ivar name: The name of the activity.
    :type name: str
    :ivar description: A brief description of the activity.
    :type description: Optional[str]
    :ivar location: The location where the activity is conducted.
    :type location: Optional[str]
    :ivar resident_price: The price of the activity for residents.
    :type resident_price: Optional[float]
    :ivar external_price: The price of the activity for non-residents/external participants.
    :type external_price: Optional[float]
    :ivar is_child_activity: Indicates whether this activity is designed for children.
    :type is_child_activity: Optional[bool]
    :ivar is_adult_activity: Indicates whether this activity is designed for adults.
    :type is_adult_activity: Optional[bool]
    :ivar max_participants: The maximum number of participants allowed in the activity.
    :type max_participants: Optional[int]
    """
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    resident_price: Optional[float] = None
    external_price: Optional[float] = None
    is_child_activity: Optional[bool] = False
    is_adult_activity: Optional[bool] = False
    max_participants: Optional[int] = 0


class ActivityCreate(ActivityBase):
    pass


class ActivitySchema(ActivityBase):
    """
        Represents an activity with participation tracking.

        This class extends the ActivityBase and includes additional attributes
        for managing participation details. It provides a mechanism to track
        the current number of participants in an activity. The class is designed
        to integrate with configuration and attribute handling provided in its
        parent or associated framework.

        :ivar id: The unique identifier for the activity.
        :type id: int
        :ivar current_participants: The current number of participants in the
            activity. Defaults to 0.
        :type current_participants: Optional[int]
    """
    id: int
    current_participants: Optional[int] = 0

    class Config:
        from_attributes = True


class AdminUserBase(BaseModel):
    username: str


class AdminUserCreate(AdminUserBase):
    password: str


class AdminUserSchema(AdminUserBase):
    id: int
    hashed_password: str

    class Config:
        from_attributes = True


class AdminUserOut(AdminUserBase):
    id: int

    class Config:
        from_attributes = True


AdhesionSchema.model_rebuild()
