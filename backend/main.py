
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional
import sqlite3
import random
import string
import json

app = FastAPI()

# CORS Middleware
origins = [
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Database setup
def get_db_connection():
    conn = sqlite3.connect('foyer_rural.db')
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    print("Creating/updating database tables...") # Debug print
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON;") # Enable foreign key support
    conn.execute('''
        CREATE TABLE IF NOT EXISTS adhesions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            numero_rue TEXT,
            nom_rue TEXT,
            code_postal TEXT,
            ville TEXT,
            adhesion_amount REAL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT DEFAULT '',
            location TEXT DEFAULT '',
            resident_price REAL DEFAULT 0.0,
            external_price REAL DEFAULT 0.0,
            is_child_activity BOOLEAN DEFAULT FALSE,
            is_adult_activity BOOLEAN DEFAULT FALSE
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS adhesion_activities (
            adhesion_id INTEGER NOT NULL,
            activity_id INTEGER NOT NULL,
            PRIMARY KEY (adhesion_id, activity_id),
            FOREIGN KEY (adhesion_id) REFERENCES adhesions(id) ON DELETE CASCADE,
            FOREIGN KEY (activity_id) REFERENCES activities(id) ON DELETE CASCADE
        )
    ''')
    
    # Insert default activities if not present
    default_activities = [
        ('danse', 'Cours de danse pour tous les âges', 'Salle Polyvalente', 100.0, 120.0, True, True),
        ('gym', 'Séances de gymnastique douce', 'Gymnase', 80.0, 100.0, False, True),
        ('pilate', 'Cours de Pilate pour renforcer le corps', 'Salle de Fitness', 90.0, 110.0, False, True)
    ]
    for name, description, location, resident_price, external_price, is_child, is_adult in default_activities:
        conn.execute('INSERT OR IGNORE INTO activities (name, description, location, resident_price, external_price, is_child_activity, is_adult_activity) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                       (name, description, location, resident_price, external_price, is_child, is_adult))

    conn.commit()
    conn.close()

create_tables()

# Pydantic models
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

class AdhesionCreate(AdhesionBase):
    pass

class Adhesion(AdhesionBase):
    id: int
    code: str
    status: str

    class Config:
        from_attributes = True

class ActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    location: Optional[str] = None
    resident_price: Optional[float] = None
    external_price: Optional[float] = None
    is_child_activity: Optional[bool] = False
    is_adult_activity: Optional[bool] = False

class ActivityCreate(ActivityBase):
    pass

class Activity(ActivityBase):
    id: int

    class Config:
        from_attributes = True

    class Config:
        from_attributes = True

# Helper function
def generate_random_code(length=8):
    letters = string.ascii_uppercase + string.digits
    return ''.join(random.choice(letters) for i in range(length))

# API Endpoints
@app.get("/api/adhesions")
def list_adhesions():
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
        adhesion_data['status'] = row['status'] # Add status
        adhesion_data['numero_rue'] = row['numero_rue']
        adhesion_data['nom_rue'] = row['nom_rue']
        adhesion_data['code_postal'] = row['code_postal']
        adhesion_data['ville'] = row['ville']
        adhesion_data['adhesion_amount'] = row['adhesion_amount']
        result.append(adhesion_data)
    conn.close()
    return result

@app.post("/api/adhesions", response_model=Adhesion)
def create_adhesion(adhesion: AdhesionCreate):
    code = generate_random_code()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO adhesions (code, email, nom, prenom, date_naissance, numero_rue, nom_rue, code_postal, ville, adhesion_amount) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (code, adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.numero_rue, adhesion.nom_rue, adhesion.code_postal, adhesion.ville, adhesion.adhesion_amount)
        )
        new_id = cursor.lastrowid

        # Insert activities
        if adhesion.activites:
            for activity_name in adhesion.activites:
                activity_id_row = conn.execute("SELECT id FROM activities WHERE name = ?", (activity_name,)).fetchone()
                if activity_id_row:
                    activity_id = activity_id_row['id']
                    conn.execute(
                        "INSERT INTO adhesion_activities (adhesion_id, activity_id) VALUES (?, ?)",
                        (new_id, activity_id)
                    )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already registered")
    finally:
        conn.close()
    
    return Adhesion(id=new_id, code=code, status="pending", **adhesion.dict())

@app.get("/api/adhesions/{code}", response_model=Adhesion)
def read_adhesion(code: str):
    conn = get_db_connection()
    adhesion_row = conn.execute("SELECT * FROM adhesions WHERE code = ?", (code,)).fetchone()
    if adhesion_row is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Adhesion not found")
    
    adhesion_data = dict(adhesion_row)
    
    # Get activities for this adhesion
    activities_rows = conn.execute(
        "SELECT a.name FROM activities a JOIN adhesion_activities aa ON a.id = aa.activity_id WHERE aa.adhesion_id = ?",
        (adhesion_data['id'],)
    ).fetchall()
    conn.close()
    
    adhesion_data['activites'] = [row['name'] for row in activities_rows]
    
    return Adhesion(**adhesion_data)

@app.put("/api/adhesions/{code}/validate", response_model=Adhesion)
def validate_adhesion(code: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE adhesions SET status = 'validated' WHERE code = ? AND status = 'pending'", (code,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Adhesion not found or already validated")
    
    updated_adhesion_row = conn.execute("SELECT * FROM adhesions WHERE code = ?", (code,)).fetchone()
    adhesion_data = dict(updated_adhesion_row)
    
    activities_rows = conn.execute(
        "SELECT a.name FROM activities a JOIN adhesion_activities aa ON a.id = aa.activity_id WHERE aa.adhesion_id = ?",
        (adhesion_data['id'],)
    ).fetchall()
    adhesion_data['activites'] = [row['name'] for row in activities_rows]
    conn.close()
    return Adhesion(**adhesion_data)

@app.put("/api/adhesions/{code}", response_model=Adhesion)
def update_adhesion(code: str, adhesion: AdhesionCreate):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if adhesion exists and get its ID
    existing_adhesion = conn.execute("SELECT id, status FROM adhesions WHERE code = ?", (code,)).fetchone()
    if existing_adhesion is None:
        conn.close()
        raise HTTPException(status_code=404, detail="Adhesion not found")
    
    adhesion_id = existing_adhesion['id']
    current_status = existing_adhesion['status']

    # Prevent updating validated adhesions
    if current_status == 'validated':
        conn.close()
        raise HTTPException(status_code=403, detail="Cannot update a validated adhesion")

    try:
        # Update adhesion details
        cursor.execute(
            "UPDATE adhesions SET email = ?, nom = ?, prenom = ?, date_naissance = ?, numero_rue = ?, nom_rue = ?, code_postal = ?, ville = ?, adhesion_amount = ? WHERE code = ?",
            (adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.numero_rue, adhesion.nom_rue, adhesion.code_postal, adhesion.ville, adhesion.adhesion_amount, code)
        )

        # Clear existing activities for this adhesion
        conn.execute("DELETE FROM adhesion_activities WHERE adhesion_id = ?", (adhesion_id,))

        # Insert new activities
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

        # Fetch the updated adhesion with its activities
        updated_adhesion = conn.execute("SELECT * FROM adhesions WHERE code = ?", (code,)).fetchone()
        activities_rows = conn.execute(
            "SELECT a.name FROM activities a JOIN adhesion_activities aa ON a.id = aa.activity_id WHERE aa.adhesion_id = ?",
            (adhesion_id,)
        ).fetchall()
        
        updated_adhesion_data = dict(updated_adhesion)
        updated_adhesion_data['activites'] = [row['name'] for row in activities_rows]

        return Adhesion(**updated_adhesion_data)
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    finally:
        conn.close()

@app.put("/api/activities/{activity_id}", response_model=Activity)
def update_activity(activity_id: int, activity: ActivityCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE activities SET name = ?, description = ?, location = ?, resident_price = ?, external_price = ?, is_child_activity = ?, is_adult_activity = ? WHERE id = ?",
        (activity.name, activity.description, activity.location, activity.resident_price, activity.external_price, activity.is_child_activity, activity.is_adult_activity, activity_id)
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    
    updated_activity = conn.execute("SELECT * FROM activities WHERE id = ?", (activity_id,)).fetchone()
    conn.close()
    return Activity(**dict(updated_activity))

@app.get("/api/activities", response_model=List[Activity])
def list_activities():
    conn = get_db_connection()
    activities = conn.execute("SELECT * FROM activities").fetchall()
    conn.close()
    result = []
    for row in activities:
        activity_data = dict(row)
        print(f"Raw activity data from DB: {activity_data}") # Debug print
        result.append(Activity(**activity_data))
    return result

@app.post("/api/activities", response_model=Activity, status_code=201)
def create_activity(activity: ActivityCreate):
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO activities (name, description, location, resident_price, external_price, is_child_activity, is_adult_activity) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING id",
                       (activity.name, activity.description, activity.location, activity.resident_price, activity.external_price, activity.is_child_activity, activity.is_adult_activity))
        new_id = cursor.fetchone()[0]
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Activity with this name already exists")
    finally:
        conn.close()
    return Activity(id=new_id, **activity.dict())

@app.delete("/api/activities/{activity_id}", status_code=204)
def delete_activity(activity_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM activities WHERE id = ?", (activity_id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Activity not found")
    conn.close()
    return

