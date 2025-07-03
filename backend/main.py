
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

def create_table():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS adhesions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            nom TEXT,
            prenom TEXT,
            date_naissance TEXT,
            adresse_postale TEXT,
            activites TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_table()

# Pydantic models
class AdhesionBase(BaseModel):
    email: EmailStr
    nom: Optional[str] = None
    prenom: Optional[str] = None
    date_naissance: Optional[str] = None
    adresse_postale: Optional[str] = None
    activites: Optional[List[str]] = None

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
    adhesions = conn.execute("SELECT * FROM adhesions").fetchall()
    conn.close()
    return [dict(row) for row in adhesions]

@app.post("/api/adhesions", response_model=Adhesion)
def create_adhesion(adhesion: AdhesionCreate):
    code = generate_random_code()
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO adhesions (code, email, nom, prenom, date_naissance, adresse_postale, activites) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.adresse_postale, json.dumps(adhesion.activites))
        )
        conn.commit()
        new_id = cursor.lastrowid
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
    conn.close()
    if adhesion_row is None:
        raise HTTPException(status_code=404, detail="Adhesion not found")
    
    adhesion_data = dict(adhesion_row)
    raw_activites = adhesion_data.pop('activites', None)
    parsed_activites = json.loads(raw_activites) if raw_activites else []
    return Adhesion(**adhesion_data, activites=parsed_activites)


@app.put("/api/adhesions/{code}", response_model=Adhesion)
def update_adhesion(code: str, adhesion: AdhesionCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE adhesions SET email = ?, nom = ?, prenom = ?, date_naissance = ?, adresse_postale = ?, activites = ? WHERE code = ?",
        (adhesion.email, adhesion.nom, adhesion.prenom, adhesion.date_naissance, adhesion.adresse_postale, json.dumps(adhesion.activites), code)
    )
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="Adhesion not found")
    
    updated_adhesion = conn.execute("SELECT * FROM adhesions WHERE code = ?", (code,)).fetchone()
    conn.close()
    
    activites = json.loads(updated_adhesion['activites']) if updated_adhesion['activites'] else None
    return Adhesion(**dict(updated_adhesion), activites=activites)
