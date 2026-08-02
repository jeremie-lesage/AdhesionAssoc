import logging
import secrets
import string
from collections import defaultdict
from datetime import date, datetime

from sqlalchemy.orm import Session, selectinload

import documents
from config import settings
from email_service import EmailSendError, send_submission_email, send_validation_email
from models import Activity, Adhesion
from models import AdminUser as Admin
from schemas import (
    ActivityCreate,
    ActivitySchema,
    ActivityStats,
    AdhesionDiscountUpdate,
    AdhesionInput,
    AdhesionSchema,
    AdminUserCreate,
    AdminUserOut,
    AdminUserSchema,
    ContactStatus,
    DashboardStats,
    FamilyDetails,
)

logger = logging.getLogger(__name__)


def generate_random_code(length=12):
    """Code d'accès d'une adhésion — son unique authentifiant.

    `secrets.choice` et non `random.choice` : ce code ouvre la lecture des
    données personnelles et la modification de l'adhésion. Le PRNG généraliste
    de Python est un Mersenne Twister, réversible depuis assez de sorties
    observées, et `POST /api/adhesions` renvoie justement le code à son auteur.
    Même idiome que le mot de passe admin de bootstrap dans `main.py`.
    """
    letters = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(letters) for _ in range(length))


# Adhesion CRUD
def get_adhesions(db: Session) -> list[AdhesionSchema]:
    adhesions = db.query(Adhesion).options(selectinload(Adhesion.activities)).all()
    return [AdhesionSchema.model_validate(adhesion) for adhesion in adhesions]


def _check_activity_is_open(activity: Activity, exclude_adhesion_id: int | None = None) -> None:
    """Refuse une activité dont la date limite est passée ou le quota atteint.

    Partagé par la création et la modification : les deux chemins mènent à une
    inscription, ils doivent opposer les mêmes refus.

    `exclude_adhesion_id` retire du décompte l'adhésion en cours de modification.
    Sans cela, un adhérent seul sur une activité complète ne pourrait plus
    corriger son dossier : sa propre inscription saturerait le quota.
    """
    if activity.registration_deadline and date.today() > activity.registration_deadline:
        raise ValueError(f"La date limite d'inscription pour l'activité '{activity.name}' est dépassée.")
    if activity.max_participants and activity.max_participants > 0:
        others = sum(1 for a in activity.adhesions if a.id != exclude_adhesion_id)
        if others >= activity.max_participants:
            raise ValueError(f"Activity '{activity.name}' has reached its maximum number of participants.")


def create_adhesion(db: Session, adhesion: AdhesionInput) -> AdhesionSchema:
    adhesion_data = adhesion.model_dump(exclude={'activities'})
    db_adhesion = Adhesion(**adhesion_data, code=generate_random_code())

    if adhesion.activities:
        activities = db.query(Activity).filter(Activity.id.in_(adhesion.activities)).all()
        for activity in activities:
            _check_activity_is_open(activity)
            db_adhesion.activities.append(activity)

    db.add(db_adhesion)
    db.commit()
    db.refresh(db_adhesion)

    # L'adhésion est enregistrée avant l'envoi : un formulaire de quatre étapes ne
    # doit jamais être perdu parce que le fournisseur d'email est en panne.
    # `submission_email_sent_at` reste alors à NULL et l'échec est journalisé.
    try:
        send_submission_email(
            email_to=db_adhesion.email,
            subject="Nous avons reçu votre demande d'adhésion",
            body={
                "prenom": db_adhesion.prenom,
                "nom": db_adhesion.nom,
                "code": db_adhesion.code,
                "resume_url": f"{settings.PUBLIC_URL}/adhesion?code={db_adhesion.code}",
                "documents": _documents_context(db_adhesion.activities),
            },
        )
        db_adhesion.submission_email_sent_at = datetime.now()
        db.commit()
        db.refresh(db_adhesion)
    except EmailSendError:
        logger.warning(
            "Adhésion %s enregistrée sans accusé de réception (envoi à %s en échec)",
            db_adhesion.code,
            db_adhesion.email,
        )

    return AdhesionSchema.model_validate(db_adhesion)


def get_adhesion_by_code(db: Session, code: str) -> AdhesionSchema | None:
    adhesion = db.query(Adhesion).options(selectinload(Adhesion.activities)).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None
    return AdhesionSchema.model_validate(adhesion)


def _documents_context(activities) -> list[dict]:
    """Documents à remplir et signer parmi ces activités.

    Une liste `{name, url}` plutôt qu'un champ ajouté aux structures d'activités
    déjà présentes dans les contextes : l'email de validation liste des activités
    avec leur prix, l'accusé de réception n'en liste aucune. Une clé commune
    permet un bloc de template identique dans les deux fichiers.

    L'URL est absolue : elle est cliquée depuis un client mail, hors de tout
    contexte de navigation.
    """
    return [
        {
            "name": activity.name,
            "url": f"{settings.PUBLIC_URL}/api/activities/{activity.id}/document",
        }
        for activity in activities
        if activity.document_filename
    ]


def _validation_email_body(adhesion: Adhesion) -> dict:
    total_cost = adhesion.adhesion_amount or 0
    activities_details = []
    for activity in adhesion.activities:
        is_resident = adhesion.ville.lower() == 'fauverney'
        price = activity.resident_price if is_resident else activity.external_price
        total_cost += price or 0
        activities_details.append({"name": activity.name, "price": price})

    return {
        "prenom": adhesion.prenom,
        "nom": adhesion.nom,
        "code": adhesion.code,
        "adhesion_amount": adhesion.adhesion_amount,
        "activities": activities_details,
        "total_cost": total_cost,
        "documents": _documents_context(adhesion.activities),
    }


async def _send_and_stamp(db: Session, adhesion: Adhesion) -> None:
    """Envoie l'email de confirmation et horodate l'envoi.

    Propage `EmailSendError` : c'est à l'appelant de décider si l'échec est
    bloquant. Le champ `email_sent_at` n'est renseigné qu'en cas de succès.
    """
    await send_validation_email(
        email_to=adhesion.email,
        subject="Confirmation de votre adhésion au Foyer Rural",
        body=_validation_email_body(adhesion),
    )
    adhesion.email_sent_at = datetime.now()
    db.commit()
    db.refresh(adhesion)


async def validate_adhesion(db: Session, code: str) -> AdhesionSchema | None:
    adhesion = db.query(Adhesion).options(selectinload(Adhesion.activities)).filter(Adhesion.code == code, Adhesion.status == 'pending').first()
    if adhesion is None:
        return None
    adhesion.status = 'validated'
    db.commit()
    db.refresh(adhesion)

    # Une panne du fournisseur d'email ne doit pas empêcher de valider une adhésion
    # en pleine période d'inscriptions. L'adhésion reste `validated` avec
    # `email_sent_at` à NULL : le back-office le signale et propose un renvoi.
    try:
        await _send_and_stamp(db, adhesion)
    except EmailSendError:
        logger.warning(
            "Adhésion %s validée sans email de confirmation (envoi à %s en échec)",
            adhesion.code,
            adhesion.email,
        )

    return AdhesionSchema.model_validate(adhesion)


async def resend_validation_email(db: Session, code: str) -> AdhesionSchema | None:
    """Renvoie l'email de confirmation d'une adhésion déjà validée.

    Laisse remonter `EmailSendError` : le renvoi est une action explicite de
    l'admin, il doit voir l'échec plutôt que de croire l'email reparti.
    """
    adhesion = db.query(Adhesion).options(selectinload(Adhesion.activities)).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None

    await _send_and_stamp(db, adhesion)
    return AdhesionSchema.model_validate(adhesion)


def invalidate_adhesion(db: Session, code: str) -> AdhesionSchema | None:
    """Repasse une adhésion en attente, quel que soit son statut de départ.

    C'est le seul retour en arrière du cycle de vie, et depuis que la
    modification est réservée au statut `pending`, le passage obligé pour
    corriger un dossier déjà validé ou encaissé. `payment_method` est effacé :
    une adhésion « en attente » qui garderait un mode de paiement serait
    affichée comme telle par le back-office.
    """
    adhesion = db.query(Adhesion).options(selectinload(Adhesion.activities)).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None
    adhesion.status = 'pending'
    adhesion.payment_method = None
    db.commit()
    db.refresh(adhesion)
    return AdhesionSchema.model_validate(adhesion)


def update_adhesion_payment(db: Session, code: str, payment_method: str) -> AdhesionSchema | None:
    adhesion = db.query(Adhesion).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None
    adhesion.status = 'paid'
    adhesion.payment_method = payment_method
    db.commit()
    db.refresh(adhesion)

    return AdhesionSchema.model_validate(adhesion)


def update_adhesion_discount(db: Session, code: str, discount: AdhesionDiscountUpdate) -> AdhesionSchema | None:
    adhesion = db.query(Adhesion).options(selectinload(Adhesion.activities)).filter(Adhesion.code == code).first()
    if adhesion is None:
        return None
    adhesion.discount_amount = discount.discount_amount
    adhesion.discount_reason = discount.discount_reason
    db.commit()
    db.refresh(adhesion)
    return AdhesionSchema.model_validate(adhesion)


def update_adhesion(db: Session, code: str, adhesion: AdhesionInput) -> AdhesionSchema | None:
    db_adhesion = db.query(Adhesion).options(selectinload(Adhesion.activities)).filter(Adhesion.code == code).first()
    if db_adhesion is None:
        return None

    # Seul le statut `pending` est modifiable. Une adhésion `validated` a fait
    # l'objet d'un email de confirmation, une `paid` d'un encaissement et d'un
    # reçu — que `GET /api/adhesions/{code}/receipt` régénère depuis l'état
    # courant, donc toute modification postérieure y apparaîtrait acquittée.
    # Pour corriger un tel dossier, un admin le repasse d'abord en attente
    # (`PUT /api/adhesions/{code}/invalidate`).
    if db_adhesion.status != 'pending':
        raise ValueError(f"Cannot update a {db_adhesion.status} adhesion")

    update_data = adhesion.model_dump(exclude_unset=True)
    activities_update = update_data.pop('activities', None)

    for key, value in update_data.items():
        setattr(db_adhesion, key, value)

    if activities_update is not None:
        db_adhesion.activities.clear()
        if adhesion.activities:
            activities = db.query(Activity).filter(Activity.id.in_(adhesion.activities)).all()
            for activity in activities:
                _check_activity_is_open(activity, exclude_adhesion_id=db_adhesion.id)
                db_adhesion.activities.append(activity)

    db.commit()
    db.refresh(db_adhesion)

    return AdhesionSchema.model_validate(db_adhesion)


def get_adherents_by_activity(db: Session, activity_id: int) -> list[AdhesionSchema]:
    activity = db.query(Activity).options(selectinload(Activity.adhesions).selectinload(Adhesion.activities)).filter(Activity.id == activity_id).first()
    if activity is None:
        raise ValueError("Activity not found")

    return [AdhesionSchema.model_validate(adhesion) for adhesion in activity.adhesions]


def delete_adhesion(db: Session, code: str) -> bool:
    adhesion = db.query(Adhesion).filter(Adhesion.code == code).first()
    if adhesion is None:
        return False
    db.delete(adhesion)
    db.commit()
    return True


# Activity CRUD
def get_activities(db: Session) -> list[ActivitySchema]:
    activities = db.query(Activity).options(selectinload(Activity.adhesions)).all()
    return [ActivitySchema.model_validate(activity) for activity in activities]


def create_activity(db: Session, activity: ActivityCreate) -> ActivitySchema:
    db_activity = Activity(**activity.model_dump())
    db.add(db_activity)
    try:
        db.commit()
        db.refresh(db_activity)
    except Exception as e:
        db.rollback()
        raise ValueError(f"Activity with name {activity.name} already exists") from e
    return ActivitySchema.model_validate(db_activity)


def update_activity(db: Session, activity_id: int, activity: ActivityCreate) -> ActivitySchema | None:
    db_activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if db_activity is None:
        return None

    for var, value in activity.model_dump(exclude_unset=True).items():
        setattr(db_activity, var, value)

    db.commit()
    db.refresh(db_activity)
    return ActivitySchema.model_validate(db_activity)


def delete_activity(db: Session, activity_id: int) -> bool:
    activity = db.query(Activity).filter(Activity.id == activity_id).first()
    if activity is None:
        return False
    # Le document suit l'activité : sans cela chaque suppression laisserait un PDF
    # orphelin dans le volume, que plus rien ne référence et que personne ne
    # viendra purger. `documents.delete` est indulgent si le fichier n'existe pas.
    documents.delete(activity_id)
    db.delete(activity)
    db.commit()
    return True


def get_activity(db: Session, activity_id: int) -> Activity | None:
    """Renvoie le modèle, pas le schéma : la route de téléchargement n'a besoin
    que de `document_filename`, et sérialiser l'activité entière serait inutile."""
    return db.query(Activity).filter(Activity.id == activity_id).first()


def store_activity_document(
    db: Session, activity_id: int, source, filename: str | None
) -> ActivitySchema:
    """Attache un document PDF à une activité.

    L'ordre compte : on vérifie d'abord que l'activité existe, sinon un upload sur
    un id inconnu écrirait un fichier orphelin que rien ne référencerait ensuite.

    Lève `ValueError` si l'activité n'existe pas, et propage `documents.NotAPdf`
    ou `documents.DocumentTooLarge` — c'est à l'appelant HTTP de les traduire.
    """
    activity = get_activity(db, activity_id)
    if activity is None:
        raise ValueError("Activity not found")

    documents.store(activity_id, source)
    activity.document_filename = documents.sanitize_filename(filename)
    db.commit()
    db.refresh(activity)
    return ActivitySchema.model_validate(activity)


def remove_activity_document(db: Session, activity_id: int) -> bool:
    """Détache le document. `False` si l'activité ou le document n'existe pas."""
    activity = get_activity(db, activity_id)
    if activity is None or activity.document_filename is None:
        return False

    documents.delete(activity_id)
    activity.document_filename = None
    db.commit()
    return True


# Admin CRUD
def get_admin(db: Session, admin_id: int) -> AdminUserSchema | None:
    return db.query(Admin).filter(Admin.id == admin_id).first()

def get_admin_by_username(db: Session, username: str) -> AdminUserSchema | None:
    return db.query(Admin).filter(Admin.username == username).first()

def get_admins(db: Session) -> list[AdminUserOut]:
    admins = db.query(Admin).all()
    return [AdminUserOut.model_validate(admin) for admin in admins]

def create_admin(db: Session, admin: AdminUserCreate) -> AdminUserOut:
    db_admin = Admin(username=admin.username, hashed_password=admin.password)
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return AdminUserOut.model_validate(db_admin)

def update_admin(db: Session, admin_id: int, admin: AdminUserCreate) -> AdminUserOut | None:
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


def get_contacts_with_status(db: Session) -> list[ContactStatus]:
    adhesions = db.query(Adhesion).all()
    contacts: dict[str, dict] = defaultdict(lambda: {"statuses": [], "telephone": None})
    for adhesion in adhesions:
        contacts[adhesion.email]["statuses"].append(adhesion.status)
        if adhesion.telephone and not contacts[adhesion.email]["telephone"]:
            contacts[adhesion.email]["telephone"] = adhesion.telephone

    contact_statuses = []
    for email, data in contacts.items():
        statuses = data["statuses"]
        if "pending" in statuses:
            status = "pending"
        elif all(s == "paid" for s in statuses):
            status = "payé"
        else:
            status = "Incomplet"
        contact_statuses.append(ContactStatus(email=email, status=status, telephone=data["telephone"]))

    return contact_statuses


def _calculate_adhesion_cost(adhesion: Adhesion) -> float:
    total_cost = adhesion.adhesion_amount or 0
    for activity in adhesion.activities:
        is_resident = adhesion.ville.lower() == 'fauverney'
        price = activity.resident_price if is_resident else activity.external_price
        total_cost += price or 0
    total_cost -= adhesion.discount_amount or 0
    return max(total_cost, 0)


def get_family_details_by_email(db: Session, email: str) -> FamilyDetails | None:
    adhesions = db.query(Adhesion).options(selectinload(Adhesion.activities)).filter(Adhesion.email == email).all()

    if not adhesions:
        return None

    total_due = 0
    adhesion_schemas = []

    for adhesion in adhesions:
        adhesion_schemas.append(AdhesionSchema.model_validate(adhesion))
        total_due += _calculate_adhesion_cost(adhesion)

    return FamilyDetails(
        email=email,
        adherents=adhesion_schemas,
        total_due=total_due
    )


def get_dashboard_stats(db: Session) -> DashboardStats:
    adhesions = db.query(Adhesion).options(selectinload(Adhesion.activities)).all()
    activities = db.query(Activity).options(selectinload(Activity.adhesions)).all()

    pending = sum(1 for a in adhesions if a.status == 'pending')
    validated = sum(1 for a in adhesions if a.status == 'validated')
    paid = sum(1 for a in adhesions if a.status == 'paid')
    contacts = len({a.email for a in adhesions})
    residents = sum(1 for a in adhesions if a.ville and a.ville.lower() == 'fauverney')
    external = len(adhesions) - residents

    children = 0
    adults = 0
    for a in adhesions:
        if a.date_naissance:
            try:
                from datetime import datetime
                birth = datetime.strptime(a.date_naissance, "%Y-%m-%d")
                age = (datetime.now() - birth).days // 365
                if age < settings.ADULT_AGE_THRESHOLD:
                    children += 1
                else:
                    adults += 1
            except ValueError:
                adults += 1
        else:
            adults += 1

    revenue_expected = sum(_calculate_adhesion_cost(a) for a in adhesions)
    revenue_collected = sum(_calculate_adhesion_cost(a) for a in adhesions if a.status == 'paid')

    activity_stats = []
    for act in activities:
        act_revenue_expected = 0.0
        act_revenue_collected = 0.0
        for adh in act.adhesions:
            is_resident = adh.ville and adh.ville.lower() == 'fauverney'
            price = (act.resident_price if is_resident else act.external_price) or 0
            act_revenue_expected += price
            if adh.status == 'paid':
                act_revenue_collected += price
        activity_stats.append(ActivityStats(
            id=act.id,
            name=act.name,
            is_child_activity=act.is_child_activity or False,
            is_adult_activity=act.is_adult_activity or False,
            max_participants=act.max_participants or 0,
            current_participants=len(act.adhesions),
            revenue_expected=act_revenue_expected,
            revenue_collected=act_revenue_collected,
        ))

    return DashboardStats(
        total_adhesions=len(adhesions),
        pending=pending,
        validated=validated,
        paid=paid,
        total_contacts=contacts,
        residents=residents,
        external=external,
        children=children,
        adults=adults,
        revenue_expected=revenue_expected,
        revenue_collected=revenue_collected,
        activities=activity_stats,
    )
