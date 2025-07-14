import sqlite3
import string
import random
from typing import List, Optional

from models import Adhesion, AdhesionCreate, Activity, ActivityCreate
from database import get_db_connection

def generate_random_code(length=12):
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for _ in range(length))


# Adhesion CRUD
def get_adhesions() -> List[Adhesion]:
    conn = get_db_connection()
    adhesions_rows = conn.execute("SELECT * FROM adhesions").fetchall()

    result = []
    for row in adhesions_rows:
        adhesion_data = dict(row)
        activities_rows = conn.execute(
            "SELECT a.name FROM activities a JOIN adhesion_activities aa ON a.id = aa.activity_id WHERE aa.adhesion_id = ?",
            (adhesion_data['id'],)
        ).fetchall()
        adhesion_data['activites'] = [r['name'] for r in activities_rows]
        adhesion_data['status'] = row['status']
        adhesion_data['numero_rue'] = row['numero_rue']
        adhesion_data['nom_rue'] = row['nom_rue']
        adhesion_data['code_postal'] = row['code_postal']
        adhesion_data['ville'] = row['ville']
        adhesion_data['adhesion_amount'] = row['adhesion_amount']
        adhesion_data['payment_method'] = row['payment_method']
        result.append(adhesion_data)
    conn.close()
    return [Adhesion(**adhesion_data) for adhesion_data in result]


def create_adhesion(adhesion: AdhesionCreate):
    code = generate_random_code()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO adhesions (code, email, nom, prenom, date_naissance, numero_rue, nom_rue, code_postal, ville, adhesion_amount, payment_method) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.numero_rue,
             adhesion.nom_rue, adhesion.code_postal, adhesion.ville, adhesion.adhesion_amount, adhesion.payment_method)
        )
        new_id = cursor.lastrowid

        if adhesion.activites:
            for activity_name in adhesion.activites:
                activity_id_row = conn.execute("SELECT id, max_participants FROM activities WHERE name = ?",
                                               (activity_name,)).fetchone()
                if activity_id_row:
                    activity_id = activity_id_row['id']
                    max_participants = activity_id_row['max_participants']

                    current_participants_row = conn.execute(
                        "SELECT COUNT(*) FROM adhesion_activities WHERE activity_id = ?", (activity_id,)).fetchone()
                    current_participants = current_participants_row[0]

                    if max_participants > 0 and current_participants >= max_participants:
                        conn.close()
                        raise ValueError(f"Activity '{activity_name}' has reached its maximum number of participants.")

                    conn.execute(
                        "INSERT INTO adhesion_activities (adhesion_id, activity_id) VALUES (?, ?)",
                        (new_id, activity_id)
                    )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Email already registered")
    finally:
        conn.close()

    return Adhesion(id=new_id, code=code, status="pending", **adhesion.dict())


def get_adhesion_by_code(code: str) -> Optional[Adhesion]:
    conn = get_db_connection()
    adhesion_row = conn.execute("SELECT * FROM adhesions WHERE code = ?", (code,)).fetchone()
    if adhesion_row is None:
        conn.close()
        return None

    adhesion_data = dict(adhesion_row)

    activities_rows = conn.execute(
        "SELECT a.name FROM activities a JOIN adhesion_activities aa ON a.id = aa.activity_id WHERE aa.adhesion_id = ?",
        (adhesion_data['id'],)
    ).fetchall()
    conn.close()

    adhesion_data['activites'] = [row['name'] for row in activities_rows]
    adhesion_data['payment_method'] = adhesion_row['payment_method']

    return Adhesion(**adhesion_data)


def validate_adhesion(code: str) -> Optional[Adhesion]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE adhesions SET status = 'validated' WHERE code = ? AND status = 'pending'", (code,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return None

    updated_adhesion_row = conn.execute("SELECT * FROM adhesions WHERE code = ?", (code,)).fetchone()
    adhesion_data = dict(updated_adhesion_row)

    activities_rows = conn.execute(
        "SELECT a.name FROM activities a JOIN adhesion_activities aa ON a.id = aa.activity_id WHERE aa.adhesion_id = ?",
        (adhesion_data['id'],)
    ).fetchall()
    adhesion_data['activites'] = [row['name'] for row in activities_rows]
    adhesion_data['payment_method'] = updated_adhesion_row['payment_method']
    conn.close()
    return Adhesion(**adhesion_data)


def update_adhesion(code: str, adhesion: AdhesionCreate) -> Optional[Adhesion]:
    conn = get_db_connection()
    cursor = conn.cursor()

    existing_adhesion = conn.execute("SELECT id, status FROM adhesions WHERE code = ?", (code,)).fetchone()
    if existing_adhesion is None:
        conn.close()
        return None

    adhesion_id = existing_adhesion['id']
    current_status = existing_adhesion['status']

    if current_status == 'validated':
        conn.close()
        raise ValueError("Cannot update a validated adhesion")

    try:
        cursor.execute(
            "UPDATE adhesions SET email = ?, nom = ?, prenom = ?, date_naissance = ?, numero_rue = ?, nom_rue = ?, code_postal = ?, ville = ?, adhesion_amount = ?, payment_method = ? WHERE code = ?",
            (adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.numero_rue,
             adhesion.nom_rue, adhesion.code_postal, adhesion.ville, adhesion.adhesion_amount, adhesion.payment_method,
             code)
        )

        conn.execute("DELETE FROM adhesion_activities WHERE adhesion_id = ?", (adhesion_id,))

        if adhesion.activites:
            for activity_name in adhesion.activites:
                activity_id_row = conn.execute("SELECT id FROM activities WHERE name = ?", (activity_name,)).fetchone()
                if activity_id_row:
                    activity_id = activity_id_row['id']
                    conn.execute(
                        "INSERT INTO adhesion_activities (adhesion_id, activity_id) VALUES (?, ?)",
                        (adhesion_id, activity_id)
                    )
        conn.commit()

        updated_adhesion = conn.execute("SELECT * FROM adhesions WHERE code = ?", (code,)).fetchone()
        activities_rows = conn.execute(
            "SELECT a.name FROM activities a JOIN adhesion_activities aa ON a.id = aa.activity_id WHERE aa.adhesion_id = ?",
            (adhesion_id,)
        ).fetchall()

        updated_adhesion_data = dict(updated_adhesion)
        updated_adhesion_data['activites'] = [row['name'] for row in activities_rows]
        updated_adhesion_data['payment_method'] = updated_adhesion['payment_method']

        return Adhesion(**updated_adhesion_data)
    except Exception as e:
        conn.close()
        raise e
    finally:
        conn.close()


def get_adherents_by_activity(activity_id: int) -> List[Adhesion]:
    conn = get_db_connection()
    activity_row = conn.execute("SELECT id FROM activities WHERE id = ?", (activity_id,)).fetchone()
    if activity_row is None:
        conn.close()
        raise ValueError("Activity not found")

    adhesions_rows = conn.execute(
        "SELECT a.* FROM adhesions a JOIN adhesion_activities aa ON a.id = aa.adhesion_id WHERE aa.activity_id = ?",
        (activity_id,)
    ).fetchall()

    result = []
    for row in adhesions_rows:
        adhesion_data = dict(row)
        activities_rows = conn.execute(
            "SELECT act.name FROM activities act JOIN adhesion_activities ad_act ON act.id = ad_act.activity_id WHERE ad_act.adhesion_id = ?",
            (adhesion_data['id'],)
        ).fetchall()
        adhesion_data['activites'] = [r['name'] for r in activities_rows]
        result.append(adhesion_data)
    conn.close()
    return [Adhesion(**adhesion_data) for adhesion_data in result]


# Activity CRUD
def update_activity(activity_id: int, activity: ActivityCreate) -> Optional[Activity]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE activities SET name = ?, description = ?, location = ?, resident_price = ?, external_price = ?, is_child_activity = ?, is_adult_activity = ?, max_participants = ? WHERE id = ?",
        (activity.name, activity.description, activity.location, activity.resident_price, activity.external_price,
         activity.is_child_activity, activity.is_adult_activity, activity.max_participants, activity_id)
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return None

    updated_activity = conn.execute("SELECT * FROM activities WHERE id = ?", (activity_id,)).fetchone()
    conn.close()
    return Activity(**dict(updated_activity))


def get_activities() -> List[Activity]:
    conn = get_db_connection()
    activities = conn.execute("SELECT * FROM activities").fetchall()
    result = []
    for row in activities:
        activity_data = dict(row)
        participants_row = conn.execute("SELECT COUNT(*) FROM adhesion_activities WHERE activity_id = ?",
                                        (activity_data['id'],)).fetchone()
        activity_data['current_participants'] = participants_row[0]
        result.append(Activity(**activity_data))
    conn.close()
    return result


def create_activity(activity: ActivityCreate) -> Activity:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO activities (name, description, location, resident_price, external_price, is_child_activity, is_adult_activity, max_participants) VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING id",
            (activity.name, activity.description, activity.location, activity.resident_price, activity.external_price,
             activity.is_child_activity, activity.is_adult_activity, activity.max_participants))
        new_id = cursor.fetchone()[0]
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise ValueError("Activity with this name already exists")
    finally:
        conn.close()
    return Activity(id=new_id, **activity.dict())


def delete_activity(activity_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        return False
    conn.close()
    return True
