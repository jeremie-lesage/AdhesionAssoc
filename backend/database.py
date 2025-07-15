import sqlite3
import os

def get_db_connection():
    DB_NAME = os.environ.get("DATABASE_NAME", "foyer_rural.db")
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    print("Creating/updating database tables...")
    conn = get_db_connection()
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS adhesions
                 (
                     id              INTEGER PRIMARY KEY AUTOINCREMENT,
                     code            TEXT UNIQUE NOT NULL,
                     email           TEXT        NOT NULL,
                     nom             TEXT,
                     prenom          TEXT,
                     date_naissance  TEXT,
                     numero_rue      TEXT,
                     nom_rue         TEXT,
                     code_postal     TEXT,
                     ville           TEXT,
                     adhesion_amount REAL,
                     payment_method  TEXT,
                     status          TEXT DEFAULT 'pending'
                 )
                 ''')
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS activities
                 (
                     id                INTEGER PRIMARY KEY AUTOINCREMENT,
                     name              TEXT UNIQUE NOT NULL,
                     description       TEXT    DEFAULT '',
                     location          TEXT    DEFAULT '',
                     resident_price    REAL    DEFAULT 0.0,
                     external_price    REAL    DEFAULT 0.0,
                     is_child_activity BOOLEAN DEFAULT FALSE,
                     is_adult_activity BOOLEAN DEFAULT FALSE,
                     max_participants  INTEGER DEFAULT 0
                 )
                 ''')
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS adhesion_activities
                 (
                     adhesion_id INTEGER NOT NULL,
                     activity_id INTEGER NOT NULL,
                     PRIMARY KEY (adhesion_id, activity_id),
                     FOREIGN KEY (adhesion_id) REFERENCES adhesions (id) ON DELETE CASCADE,
                     FOREIGN KEY (activity_id) REFERENCES activities (id) ON DELETE CASCADE
                 )
                 ''')
    conn.execute('''
                 CREATE TABLE IF NOT EXISTS admins
                 (
                     id             INTEGER PRIMARY KEY AUTOINCREMENT,
                     username       TEXT UNIQUE NOT NULL,
                     hashed_password TEXT NOT NULL
                 )
                 ''')

    default_activities = [
        ('danse', 'Cours de danse pour tous les âges', 'Salle Polyvalente', 100.0, 120.0, True, True),
        ('gym', 'Séances de gymnastique douce', 'Gymnase', 80.0, 100.0, False, True),
        ('pilate', 'Cours de Pilate pour renforcer le corps', 'Salle de Fitness', 90.0, 110.0, False, True)
    ]
    for name, description, location, resident_price, external_price, is_child, is_adult in default_activities:
        conn.execute(
            'INSERT OR IGNORE INTO activities (name, description, location, resident_price, external_price, is_child_activity, is_adult_activity) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (name, description, location, resident_price, external_price, is_child, is_adult))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    create_tables()
