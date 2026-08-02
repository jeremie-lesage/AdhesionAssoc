from datetime import date, datetime, time

from pydantic import BaseModel, EmailStr


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
    description: str | None = None
    location: str | None = None
    resident_price: float | None = None
    external_price: float | None = None
    is_child_activity: bool | None = False
    is_adult_activity: bool | None = False
    max_participants: int | None = 0
    registration_deadline: date | None = None
    day_of_week: int | None = None
    start_time: time | None = None
    end_time: time | None = None


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
    current_participants: int | None = 0
    # En sortie seulement, volontairement absent d'`ActivityBase` : `ActivityCreate`
    # sert de corps au `PUT /api/activities/{id}`, et si le champ y figurait un admin
    # pourrait faire pointer la colonne vers un nom arbitraire sans qu'aucun fichier
    # change. La colonne n'est écrite que par les routes de document.
    document_filename: str | None = None

    class Config:
        from_attributes = True


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
    :ivar nom_rue: The street number and name of the individual's address.
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
    telephone: str | None = None
    nom: str | None = None
    prenom: str | None = None
    date_naissance: str | None = None
    nom_rue: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    adhesion_amount: float | None = None
    payment_method: str | None = None
    discount_amount: float | None = 0
    discount_reason: str | None = None


class AdhesionInput(BaseModel):
    """Champs saisis par l'adhérent — entrée de POST et PUT /api/adhesions.

    Volontairement disjoint d'`AdhesionBase` : `discount_amount`, `discount_reason`
    et `payment_method` n'y figurent pas. Ces champs ne se posent que par les routes
    admin dédiées (`/discount`, `/pay`), toutes deux derrière `get_current_admin` ;
    les hériter ici rouvrirait le contournement de ce contrôle par la route publique.

    Les champs inconnus sont ignorés, pas rejetés : le formulaire renvoie tout son
    état (`code`, `status`, et le reste de l'adhésion rechargée en modification).
    """
    email: EmailStr
    telephone: str | None = None
    nom: str | None = None
    prenom: str | None = None
    date_naissance: str | None = None
    nom_rue: str | None = None
    code_postal: str | None = None
    ville: str | None = None
    adhesion_amount: float | None = None
    activities: list[int] | None = []


class AdhesionSchema(AdhesionBase):
    id: int
    code: str
    status: str
    # NULL sur une adhésion validée : l'email de confirmation n'a pas pu être envoyé.
    email_sent_at: datetime | None = None
    # NULL : l'accusé de réception de la soumission n'a pas pu être envoyé.
    submission_email_sent_at: datetime | None = None
    activities: list[ActivitySchema] = []

    class Config:
        from_attributes = True


class AdhesionPaymentUpdate(BaseModel):
    payment_method: str


class AdhesionDiscountUpdate(BaseModel):
    discount_amount: float
    discount_reason: str | None = None


# Pydantic models for Admin
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


class ContactStatus(BaseModel):
    email: EmailStr
    status: str
    telephone: str | None = None


class FamilyDetails(BaseModel):
    email: EmailStr
    adherents: list[AdhesionSchema]
    total_due: float


AdhesionSchema.model_rebuild()


class ActivityStats(BaseModel):
    id: int
    name: str
    is_child_activity: bool
    is_adult_activity: bool
    max_participants: int
    current_participants: int
    revenue_expected: float
    revenue_collected: float

class DashboardStats(BaseModel):
    total_adhesions: int
    pending: int
    validated: int
    paid: int
    total_contacts: int
    residents: int
    external: int
    children: int
    adults: int
    revenue_expected: float
    revenue_collected: float
    activities: list[ActivityStats]


class PublicSettings(BaseModel):
    iban: str
    bic: str
    bank: str
    postal_code_prefix: str
    adult_age_threshold: int
