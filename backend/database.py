import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://user:password@localhost:5432/foyer_rural_db")
engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    print("Creating/updating database tables...")
    Base.metadata.create_all(engine)

    db = SessionLocal()
    default_activities_data = [
    ]

    for activity_data in default_activities_data:
        existing_activity = db.query(Activity).filter_by(name=activity_data['name']).first()
        if not existing_activity:
            activity = Activity(**activity_data)
            db.add(activity)
    db.commit()
    db.close()


if __name__ == "__main__":
    create_tables()
