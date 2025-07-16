import string
import random
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import Adhesion, Activity, AdhesionActivity, Admin
from models import AdhesionCreate, ActivityCreate, AdminUserCreate, AdminUser, Adhesion as PydanticAdhesion, Activity as PydanticActivity, AdminUserOut


def generate_random_code(length=12):
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


# Adhesion CRUD
def get_adhesions(db: Session) -> List[PydanticAdhesion]:
    adhesions = db.query(Adhesion).all()
    result = []
    for adhesion in adhesions:
        adhesion_data = PydanticAdhesion.model_validate(adhesion)
        adhesion_data.activites = [activity.id for activity in adhesion.activities]
        result.append(adhesion_data)
    return result


def create_adhesion(db: Session, adhesion: AdhesionCreate) -> PydanticAdhesion:
    adhesion_data = adhesion.model_dump(exclude={'activites'})
    db_adhesion = Adhesion(**adhesion_data, code=generate_random_code())

    if adhesion.activites:
        for activity_id in adhesion.activites:
            activity = db.query(Activity).filter(Activity.id == activity_id).first()
            if activity:
                current_participants = db.query(func.count(AdhesionActivity.adhesion_id)).filter(AdhesionActivity.activity_id == activity.id).scalar()
                if activity.max_participants > 0 and current_participants >= activity.max_participants:
                    raise ValueError(f"Activity '{activity.name}' has reached its maximum number of participants.")
                db_adhesion.activities.append(activity)

    db.add(db_adhesion)
    db.commit()
    db.refresh(db_adhesion)

    response_model = PydanticAdhesion.model_validate(db_adhesion)
    response_model.activites = [activity.id for activity in db_adhesion.activities]
    return response_model


from email_service import send_validation_email

def get_adhesion_by_code(db: Session, code: str) -> Optional[PydanticAdhesion]:
    adhesion = db.query(Adhesion).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None

    response_model = PydanticAdhesion.model_validate(adhesion)
    response_model.activites = [activity.id for activity in adhesion.activities]
    return response_model


async def validate_adhesion(db: Session, code: str) -> Optional[PydanticAdhesion]:
    adhesion = db.query(Adhesion).filter(Adhesion.code == code, Adhesion.status == 'pending').first()
    if adhesion is None:
        return None
    adhesion.status = 'validated'
    
    total_cost = adhesion.adhesion_amount or 0
    activities_details = []
    for activity in adhesion.activities:
        is_resident = adhesion.ville.lower() == 'fauverney'
        price = activity.resident_price if is_resident else activity.external_price
        total_cost += price or 0
        activities_details.append({"name": activity.name, "price": price})

    db.commit()
    db.refresh(adhesion)

    email_body = {
        "prenom": adhesion.prenom,
        "nom": adhesion.nom,
        "code": adhesion.code,
        "adhesion_amount": adhesion.adhesion_amount,
        "activities": activities_details,
        "total_cost": total_cost,
    }
    await send_validation_email(
        email_to=adhesion.email,
        subject="Confirmation de votre adhésion au Foyer Rural",
        body=email_body
    )

    response_model = PydanticAdhesion.model_validate(adhesion)
    response_model.activites = [activity.id for activity in adhesion.activities]
    return response_model


def update_adhesion_payment(db: Session, code: str, payment_method: str) -> Optional[PydanticAdhesion]:
    adhesion = db.query(Adhesion).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None
    adhesion.status = 'paid'
    adhesion.payment_method = payment_method
    db.commit()
    db.refresh(adhesion)

    response_model = PydanticAdhesion.model_validate(adhesion)
    response_model.activites = [activity.id for activity in adhesion.activities]
    return response_model


def update_adhesion(db: Session, code: str, adhesion: AdhesionCreate) -> Optional[PydanticAdhesion]:
    db_adhesion = db.query(Adhesion).filter(Adhesion.code == code).first()
    if db_adhesion is None:
        return None

    if db_adhesion.status == 'validated':
        raise ValueError("Cannot update a validated adhesion")

    update_data = adhesion.model_dump(exclude_unset=True, exclude={'activites'})
    for key, value in update_data.items():
        setattr(db_adhesion, key, value)

    db_adhesion.activities.clear()
    if adhesion.activites:
        for activity_id in adhesion.activites:
            activity = db.query(Activity).filter(Activity.id == activity_id).first()
            if activity:
                db_adhesion.activities.append(activity)

    db.commit()
    db.refresh(db_adhesion)

    response_model = PydanticAdhesion.model_validate(db_adhesion)
    response_model.activites = [activity.id for activity in db_adhesion.activities]
    return response_model


def get_adherents_by_activity(db: Session, activity_id: int) -> List[PydanticAdhesion]:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity is None:
        raise ValueError("Activity not found")

    adhesions = activity.adhesions
    result = []
    for adhesion in adhesions:
        adhesion_data = PydanticAdhesion.model_validate(adhesion)
        adhesion_data.activites = [act.id for act in adhesion.activities]
        result.append(adhesion_data)
    return result


# Activity CRUD
def get_activities(db: Session) -> List[PydanticActivity]:
    activities = db.query(Activity).all()
    result = []
    for activity in activities:
        current_participants = db.query(func.count(AdhesionActivity.adhesion_id)).filter(AdhesionActivity.activity_id == activity.id).scalar()
        activity_data = activity.__dict__
        activity_data['current_participants'] = current_participants
        result.append(PydanticActivity(**activity_data))
    return result


def create_activity(db: Session, activity: ActivityCreate) -> PydanticActivity:
    db_activity = Activity(**activity.model_dump())
    db.add(db_activity)
    try:
        db.commit()
        db.refresh(db_activity)
    except Exception:
        db.rollback()
        raise ValueError(f"Activity with name {activity.name} already exists")
    return PydanticActivity(**db_activity.__dict__)


def update_activity(db: Session, activity_id: int, activity: ActivityCreate) -> Optional[PydanticActivity]:
    db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if db_activity is None:
        return None

    for var, value in activity.model_dump(exclude_unset=True).items():
        setattr(db_activity, var, value)

    db.commit()
    db.refresh(db_activity)
    return PydanticActivity(**db_activity.__dict__)


def delete_activity(db: Session, activity_id: int) -> bool:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity is None:
        return False
    db.delete(activity)
    db.commit()
    return True


# Admin CRUD
def get_admin(db: Session, admin_id: int) -> Optional[AdminUser]:
    return db.query(Admin).filter(Admin.id == admin_id).first()

def get_admin_by_username(db: Session, username: str) -> Optional[AdminUser]:
    return db.query(Admin).filter(Admin.username == username).first()

def get_admins(db: Session) -> List[AdminUserOut]:
    admins = db.query(Admin).all()
    return [AdminUserOut.model_validate(admin) for admin in admins]

def create_admin(db: Session, admin: AdminUserCreate) -> AdminUserOut:
    db_admin = Admin(username=admin.username, hashed_password=admin.password)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return AdminUserOut.model_validate(db_admin)

def update_admin(db: Session, admin_id: int, admin: AdminUserCreate) -> Optional[AdminUserOut]:
    db_admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if db_admin is None:
        return None
    db_admin.username = admin.username
    db_admin.hashed_password = admin.password
    db.commit()
    db.refresh(db_admin)
    return AdminUserOut.model_validate(db_admin)

def delete_admin(db: Session, admin_id: int) -> bool:
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin is None:
        return False
    db.delete(admin)
    db.commit()
    return True
