
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
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS adhesions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            adresse_postale TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
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
    default_activities = ['danse', 'gym', 'pilate']
    for activity_name in default_activities:
        conn.execute('INSERT OR IGNORE INTO activities (name) VALUES (?)', (activity_name,))

    conn.commit()
    conn.close()

create_tables()

# Pydantic models
class AdhesionBase(BaseModel):
    email: EmailStr
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[str] = None
    adresse_postale: Optional[str] = None
    activites: Optional[List[str]] = []

class AdhesionCreate(AdhesionBase):
    pass

class Adhesion(AdhesionBase):
    id: int
    code: str

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
            "INSERT INTO adhesions (code, email, nom, prenom, date_naissance, adresse_postale) VALUES (?, ?, ?, ?, ?, ?)",
            (code, adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.adresse_postale)
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
    
    return Adhesion(id=new_id, code=code, **adhesion.dict())

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


@app.put("/api/adhesions/{code}", response_model=Adhesion)
def update_adhesion(code: str, adhesion: AdhesionCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update adhesion details
    cursor.execute(
        "UPDATE adhesions SET email = ?, nom = ?, prenom = ?, date_naissance = ?, adresse_postale = ? WHERE code = ?",
        (adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.adresse_postale, code)
    )
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Adhesion not found")

    updated_adhesion_row = conn.execute("SELECT id FROM adhesions WHERE code = ?", (code,)).fetchone()
    adhesion_id = updated_adhesion_row['id']

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
    conn.close()
    
    updated_adhesion_data = dict(updated_adhesion)
    updated_adhesion_data['activites'] = [row['name'] for row in activities_rows]

    return Adhesion(**updated_adhesion_data)
