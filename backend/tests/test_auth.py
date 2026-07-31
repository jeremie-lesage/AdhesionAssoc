"""Tests de la couche d'authentification (`auth.py`).

Les contrôles d'autorisation vus depuis HTTP sont dans test_api.py ; ici on teste
l'émission du jeton et l'empreinte d'identifiants, sans passer par l'application.
"""

from datetime import UTC, datetime, timedelta

from jose import jwt

from auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    credentials_fingerprint,
    get_password_hash,
)


def _decode(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


class TestAccessTokenExpiry:
    def test_the_default_expiry_follows_the_module_constant(self):
        """`ACCESS_TOKEN_EXPIRE_MINUTES` était une constante morte : la durée
        réelle venait d'un `timedelta(minutes=15)` en dur dans la fonction."""
        before = datetime.now(UTC)

        payload = _decode(create_access_token({"sub": "admin"}))

        expected = before + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        actual = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert abs((actual - expected).total_seconds()) < 5

    def test_an_explicit_delta_still_wins(self):
        before = datetime.now(UTC)

        payload = _decode(create_access_token({"sub": "admin"}, timedelta(minutes=1)))

        actual = datetime.fromtimestamp(payload["exp"], tz=UTC)
        assert abs((actual - (before + timedelta(minutes=1))).total_seconds()) < 5


class TestCredentialsFingerprint:
    """L'empreinte lie le jeton au mot de passe stocké au moment de l'émission."""

    def test_it_is_stable_for_a_given_hash(self):
        hashed = get_password_hash("mot-de-passe")

        assert credentials_fingerprint(hashed) == credentials_fingerprint(hashed)

    def test_it_differs_after_rehashing_the_same_password(self):
        """bcrypt resèle : redéfinir le même mot de passe invalide les jetons.

        C'est voulu — « changement de mot de passe » doit révoquer, que le
        nouveau soit identique à l'ancien ou non.
        """
        first = credentials_fingerprint(get_password_hash("mot-de-passe"))
        second = credentials_fingerprint(get_password_hash("mot-de-passe"))

        assert first != second

    def test_it_does_not_expose_the_stored_hash(self):
        """Le jeton est lisible par son porteur : l'empreinte n'en révèle rien."""
        hashed = get_password_hash("mot-de-passe")

        fingerprint = credentials_fingerprint(hashed)

        assert hashed not in fingerprint
        assert fingerprint not in hashed
        assert len(fingerprint) == 16
