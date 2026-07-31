import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

import crud
from database import get_db

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def credentials_fingerprint(hashed_password: str) -> str:
    """Empreinte du mot de passe stocké, recopiée dans le jeton à l'émission.

    bcrypt resèle à chaque hachage : redéfinir le mot de passe — même à
    l'identique — change le hash, donc l'empreinte, donc invalide les jetons déjà
    émis. Aucune colonne de version à maintenir, et rien à incrémenter dans les
    chemins qui modifient les identifiants.

    Tronquée à 16 hexadécimaux : le jeton est lisible par son porteur, on n'y met
    que ce qu'il faut pour comparer, sans exposer le hash bcrypt.
    """
    return hashlib.sha256(hashed_password.encode()).hexdigest()[:16]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    # `ACCESS_TOKEN_EXPIRE_MINUTES` était une constante morte : la durée réelle
    # venait d'un `timedelta(minutes=15)` en dur, d'où un écart entre le réglage
    # affiché et le comportement.
    expire = datetime.now(UTC) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str, credentials_exception) -> dict:
    """Vérifie la signature et l'expiration, puis renvoie le payload.

    Renvoie le payload entier et non le seul `sub` : `get_current_admin` a aussi
    besoin de l'empreinte d'identifiants pour décider.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError as e:
        raise credentials_exception from e

    if not payload.get("sub"):
        raise credentials_exception
    return payload


def get_current_admin(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """Valide le jeton *et* l'état du compte qu'il désigne.

    Se contenter de la signature laissait un jeton pleinement valide après
    suppression du compte ou changement de mot de passe, jusqu'à son expiration :
    un administrateur dont on retirait les droits conservait un accès complet au
    back-office pendant toute cette fenêtre.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = verify_token(token, credentials_exception)

    admin = crud.get_admin_by_username(db, payload["sub"])
    if admin is None:
        raise credentials_exception

    # `compare_digest` : comparaison à temps constant, l'empreinte dérive d'un
    # secret. `get("pv", "")` couvre les jetons émis avant ce correctif, qui n'ont
    # pas le claim et doivent être refusés.
    expected = credentials_fingerprint(admin.hashed_password)
    if not secrets.compare_digest(payload.get("pv", ""), expected):
        raise credentials_exception

    return admin