import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# It's better to use the same DATABASE_URL from your application's environment
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/foyer_rural_db")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_database_state():
    db = SessionLocal()
    try:
        print("--- Vérification de l'état de la base de données ---")

        # 1. Vérifier la table des adhésions
        print("\n[+] Contenu de la table 'adhesions':")
        adhesions = db.execute(text("SELECT id, code, nom, prenom, status FROM adhesions ORDER BY id DESC LIMIT 10")).fetchall()
        if not adhesions:
            print("  -> La table 'adhesions' est vide.")
        else:
            for adhesion in adhesions:
                print(f"  - ID: {adhesion[0]}, Code: {adhesion[1]}, Nom: {adhesion[2]}, Prénom: {adhesion[3]}, Status: {adhesion[4]}")

        # 2. Vérifier la table d'association
        print("\n[+] Contenu de la table 'adhesion_activities':")
        links = db.execute(text("SELECT adhesion_id, activity_id FROM adhesion_activities ORDER BY adhesion_id DESC, activity_id ASC LIMIT 20")).fetchall()
        if not links:
            print("  -> La table 'adhesion_activities' est vide.")
        else:
            for link in links:
                print(f"  - Adhesion ID: {link[0]}, Activity ID: {link[1]}")

        print("\n--- Fin de la vérification ---")

    except Exception as e:
        print(f"\nUne erreur est survenue lors de la connexion ou de la lecture de la base de données: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_state()
