from backend.database import Base, engine, SessionLocal, Activity

def reset_database():
    print("ATTENTION: Cette opération va supprimer toutes les données existantes.")
    confirm = input("Êtes-vous sûr de vouloir continuer ? (oui/non): ")
    if confirm.lower() != 'oui':
        print("Opération annulée.")
        return

    print("Suppression de toutes les tables...")
    Base.metadata.drop_all(bind=engine)
    print("Tables supprimées.")

    print("Création de nouvelles tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables créées.")

    # Recréer les activités par défaut
    db = SessionLocal()
    try:
        print("Ajout des activités par défaut...")
        default_activities_data = [
            {'name': 'danse', 'description': 'Cours de danse pour tous les âges', 'location': 'Salle Polyvalente', 'resident_price': 100.0, 'external_price': 120.0, 'is_child_activity': True, 'is_adult_activity': True},
            {'name': 'gym', 'description': 'Séances de gymnastique douce', 'location': 'Gymnase', 'resident_price': 80.0, 'external_price': 100.0, 'is_child_activity': False, 'is_adult_activity': True},
            {'name': 'pilate', 'description': 'Cours de Pilate pour renforcer le corps', 'location': 'Salle de Fitness', 'resident_price': 90.0, 'external_price': 110.0, 'is_child_activity': False, 'is_adult_activity': True}
        ]
        for activity_data in default_activities_data:
            activity = Activity(**activity_data)
            db.add(activity)
        db.commit()
        print("Activités par défaut ajoutées.")
    finally:
        db.close()

    print("\nRéinitialisation de la base de données terminée avec succès.")

if __name__ == "__main__":
    reset_database()
