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
        activities = db.query(Activity.name).join(AdhesionActivity).filter(AdhesionActivity.adhesion_id == adhesion.id).all()
        adhesion_data = adhesion.__dict__
        adhesion_data['activites'] = [activity.name for activity in activities]
        result.append(PydanticAdhesion(**adhesion_data))
    return result


def create_adhesion(db: Session, adhesion: AdhesionCreate) -> PydanticAdhesion:
    code = generate_random_code()
    db_adhesion = Adhesion(
        code=code,
        email=adhesion.email,
        nom=adhesion.nom,
        prenom=adhesion.prenom,
        date_naissance=adhesion.date_naissance,
        numero_rue=adhesion.numero_rue,
        nom_rue=adhesion.nom_rue,
        code_postal=adhesion.code_postal,
        ville=adhesion.ville,
        adhesion_amount=adhesion.adhesion_amount,
        payment_method=adhesion.payment_method
    )
    db.add(db_adhesion)
    db.commit()
    db.refresh(db_adhesion)

    if adhesion.activites:
        for activity_name in adhesion.activites:
            activity = db.query(Activity).filter(Activity.name == activity_name).first()
            if activity:
                current_participants = db.query(func.count(AdhesionActivity.adhesion_id)).filter(AdhesionActivity.activity_id == activity.id).scalar()
                if 0 < activity.max_participants <= current_participants:
                    db.rollback()
                    raise ValueError(f"Activity '{activity_name}' has reached its maximum number of participants.")

                db_adhesion_activity = AdhesionActivity(adhesion_id=db_adhesion.id, activity_id=activity.id)
                db.add(db_adhesion_activity)
        db.commit()
        db.refresh(db_adhesion)

    adhesion_data = db_adhesion.__dict__
    activities = db.query(Activity.name).join(AdhesionActivity).filter(AdhesionActivity.adhesion_id == db_adhesion.id).all()
    adhesion_data['activites'] = [activity.name for activity in activities]
    return PydanticAdhesion(**adhesion_data)


def get_adhesion_by_code(db: Session, code: str) -> Optional[PydanticAdhesion]:
    adhesion = db.query(Adhesion).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None

    activities = db.query(Activity.name).join(AdhesionActivity).filter(AdhesionActivity.adhesion_id == adhesion.id).all()
    adhesion_data = adhesion.__dict__
    adhesion_data['activites'] = [activity.name for activity in activities]
    return PydanticAdhesion(**adhesion_data)


def validate_adhesion(db: Session, code: str) -> Optional[PydanticAdhesion]:
    adhesion = db.query(Adhesion).filter(Adhesion.code == code, Adhesion.status == 'pending').first()
    if adhesion is None:
        return None
    adhesion.status = 'validated'
    db.commit()
    db.refresh(adhesion)

    activities = db.query(Activity.name).join(AdhesionActivity).filter(AdhesionActivity.adhesion_id == adhesion.id).all()
    adhesion_data = adhesion.__dict__
    adhesion_data['activites'] = [activity.name for activity in activities]
    return PydanticAdhesion(**adhesion_data)


def update_adhesion(db: Session, code: str, adhesion: AdhesionCreate) -> Optional[PydanticAdhesion]:
    db_adhesion = db.query(Adhesion).filter(Adhesion.code == code).first()
    if db_adhesion is None:
        return None

    if db_adhesion.status == 'validated':
        raise ValueError("Cannot update a validated adhesion")

    for var, value in adhesion.model_dump(exclude_unset=True).items():
        if var != "activites": # activites are handled separately
            setattr(db_adhesion, var, value)

    db.query(AdhesionActivity).filter(AdhesionActivity.adhesion_id == db_adhesion.id).delete()
    if adhesion.activites:
        for activity_name in adhesion.activites:
            activity = db.query(Activity).filter(Activity.name == activity_name).first()
            if activity:
                db_adhesion_activity = AdhesionActivity(adhesion_id=db_adhesion.id, activity_id=activity.id)
                db.add(db_adhesion_activity)
    db.commit()
    db.refresh(db_adhesion)

    activities = db.query(Activity.name).join(AdhesionActivity).filter(AdhesionActivity.adhesion_id == db_adhesion.id).all()
    adhesion_data = db_adhesion.__dict__
    adhesion_data['activites'] = [activity.name for activity in activities]
    return PydanticAdhesion(**adhesion_data)


def get_adherents_by_activity(db: Session, activity_id: int) -> List[PydanticAdhesion]:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity is None:
        raise ValueError("Activity not found")

    adhesions = db.query(Adhesion).join(Adhesion.adhesion_activities_link).filter(AdhesionActivity.activity_id == activity_id).all()

    result = []
    for adhesion in adhesions:
        activities = db.query(Activity.name).join(AdhesionActivity).filter(AdhesionActivity.adhesion_id == adhesion.id).all()
        adhesion_data = adhesion.__dict__
        adhesion_data['activites'] = [activity.name for activity in activities]
        result.append(PydanticAdhesion(**adhesion_data))
    return result


# Activity CRUD
def update_activity(db: Session, activity_id: int, activity: ActivityCreate) -> Optional[PydanticActivity]:
    db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if db_activity is None:
        return None

    for var, value in activity.model_dump(exclude_unset=True).items():
        setattr(db_activity, var, value)

    db.commit()
    db.refresh(db_activity)
    return PydanticActivity(**db_activity.__dict__)


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
    except Exception as e:
        db.rollback()
        raise ValueError(f"Activity with name {activity.name} already exists")
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
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin is None:
        return None
    return AdminUser(**admin.__dict__)


def get_admin_by_username(db: Session, username: str) -> Optional[AdminUser]:
    admin = db.query(Admin).filter(Admin.username == username).first()
    if admin is None:
        return None
    return AdminUser(**admin.__dict__)


def get_admins(db: Session) -> List[AdminUserOut]:
    admins = db.query(Admin).all()
    return [AdminUserOut(**admin.__dict__) for admin in admins]


def create_admin(db: Session, admin: AdminUserCreate) -> AdminUserOut:
    db_admin = Admin(username=admin.username, hashed_password=admin.password) # password will be hashed before calling this
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return AdminUserOut(**db_admin.__dict__)


def update_admin(db: Session, admin_id: int, admin: AdminUserCreate) -> Optional[AdminUserOut]:
    db_admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if db_admin is None:
        return None
    db_admin.username = admin.username
    db_admin.hashed_password = admin.password # password will be hashed before calling this
    db.commit()
    db.refresh(db_admin)
    return AdminUserOut(**db_admin.__dict__)


def delete_admin(db: Session, admin_id: int) -> bool:
    admin = db.query(Admin).filter(Admin.id == admin_id).first()
    if admin is None:
        return False
    db.delete(admin)
    db.commit()
    return True