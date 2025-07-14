from pydantic import BaseModel, EmailStr
from typing import List, Optional


# Pydantic model for admin login
class AdminLogin(BaseModel):
    username: str
    password: str


# Pydantic models for Adhesion
class AdhesionBase(BaseModel):
    email: EmailStr
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[str] = None
    numero_rue: Optional[str] = None
    nom_rue: Optional[str] = None
    code_postal: Optional[str] = None
    ville: Optional[str] = None
    adhesion_amount: Optional[float] = None
    activites: Optional[List[str]] = []
    payment_method: Optional[str] = None


class AdhesionCreate(AdhesionBase):
    pass


class Adhesion(AdhesionBase):
    id: int
    code: str
    status: str
    payment_method: Optional[str] = None

    class Config:
        from_attributes = True


# Pydantic models for Activity
class ActivityBase(BaseModel):
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


class Activity(ActivityBase):
    id: int
    current_participants: Optional[int] = 0

    class Config:
        from_attributes = True
