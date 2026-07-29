"""Fixtures partagées par les tests backend.

Le schéma est créé une seule fois par session dans une base SQLite en mémoire ;
chaque test s'exécute dans une transaction annulée à la sortie. Les tests sont
donc isolés sans payer un `create_all` à chaque fonction, et aucun fichier
`test.db` n'est laissé dans le répertoire de travail.
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models import Base

# Doit être fait avant tout import de `auth` / `main` (via les fixtures plus bas) :
# auth.py lève une RuntimeError si SECRET_KEY est absent, et database.py construit
# son engine à l'import depuis DATABASE_URL. `setdefault` laisse la main à
# l'environnement s'il est déjà positionné (cf. la tâche mise `test:backend`).
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-used-in-production")
os.environ.setdefault("DATABASE_URL", "sqlite://")

ADMIN_USERNAME = "admin-test"
ADMIN_PASSWORD = "mot-de-passe-de-test"


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


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    """Le compteur de `rate_limiter` est un dict de module, donc partagé entre tests.

    Sans remise à zéro, le 6e appel à un endpoint public renverrait 429 dans un
    test qui n'a rien demandé — et l'ordre des tests changerait le résultat.
    """
    import rate_limiter

    rate_limiter.request_counts.clear()
    yield
    rate_limiter.request_counts.clear()


@pytest.fixture(autouse=True)
def sent_emails(monkeypatch):
    """Intercepte les envois d'emails et renvoie la liste des appels.

    Autouse volontairement : aucun test ne doit pouvoir appeler l'API Brevo.
    """
    import crud

    calls = []

    async def _fake_send(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(crud, "send_validation_email", _fake_send)
    return calls


@pytest.fixture
def client(db_session):
    """TestClient avec `get_db` redirigé vers la session de test.

    Le client n'est volontairement pas utilisé comme context manager : cela
    déclencherait le lifespan de FastAPI, dont le `startup_event` applique les
    migrations Alembic sur la vraie base.
    """
    from fastapi.testclient import TestClient

    import main
    from database import get_db

    main.app.dependency_overrides[get_db] = lambda: db_session
    try:
        yield TestClient(main.app)
    finally:
        main.app.dependency_overrides.clear()


@pytest.fixture
def admin_user(db_session):
    """Crée un admin et renvoie ses identifiants en clair.

    `crud.create_admin` stocke `password` tel quel dans `hashed_password` : c'est
    à l'appelant de hacher (comme le fait `startup_event`).
    """
    import crud
    from auth import get_password_hash
    from schemas import AdminUserCreate

    crud.create_admin(
        db_session,
        AdminUserCreate(username=ADMIN_USERNAME, password=get_password_hash(ADMIN_PASSWORD)),
    )
    return ADMIN_USERNAME, ADMIN_PASSWORD


@pytest.fixture
def auth_headers(client, admin_user):
    """En-tête Authorization obtenu par un vrai passage par /api/token."""
    username, password = admin_user
    response = client.post("/api/token", data={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return {"Authorization": f"Bearer {response.json()['access_token']}"}
