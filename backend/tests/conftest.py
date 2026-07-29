"""Fixtures partagées par les tests backend.

Le schéma est créé une seule fois par session dans une base SQLite en mémoire ;
chaque test s'exécute dans une transaction annulée à la sortie. Les tests sont
donc isolés sans payer un `create_all` à chaque fonction, et aucun fichier
`test.db` n'est laissé dans le répertoire de travail.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base


@pytest.fixture(scope="session")
def db_engine():
    # StaticPool : toutes les connexions réutilisent le même handle SQLite, sans
    # quoi chaque `connect()` ouvrirait une base en mémoire vide et distincte.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
