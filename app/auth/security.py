"""Investigator password check and signed, expiring session tokens."""
import base64
import getpass
import hashlib
import hmac
import os
import time

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

TOKEN_TTL_SECONDS = 3600
_hasher = PasswordHasher()


class AuthNotConfigured(Exception):
    """Required environment settings are missing."""


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


def _secret() -> bytes:
    value = os.getenv("SILENTLINE_AUTH_SECRET")
    if not value:
        raise AuthNotConfigured("SILENTLINE_AUTH_SECRET is not set")
    return value.encode()


def check_credentials(username: str, password: str) -> bool:
    expected_user = os.getenv("SILENTLINE_INVESTIGATOR_USERNAME")
    password_hash = os.getenv("SILENTLINE_INVESTIGATOR_PASSWORD_HASH")
    if not expected_user or not password_hash:
        raise AuthNotConfigured("investigator login is not configured")

    user_ok = hmac.compare_digest(username.encode(), expected_user.encode())
    try:
        _hasher.verify(password_hash, password)  # always runs, so timing doesn't reveal the username
        pass_ok = True
    except (VerificationError, InvalidHashError):
        pass_ok = False
    return user_ok and pass_ok


def create_token(username: str, now: float | None = None) -> str:
    expires = int((time.time() if now is None else now) + TOKEN_TTL_SECONDS)
    payload = f"{username}:{expires}".encode()
    sig = hmac.new(_secret(), payload, hashlib.sha256).digest()
    return f"{_b64(payload)}.{_b64(sig)}"


def verify_token(token: str, now: float | None = None) -> str | None:
    """Return the username if the token is valid and not expired, else None."""
    try:
        payload_part, sig_part = token.split(".")
        payload = _unb64(payload_part)
        sig = _unb64(sig_part)
        expected = hmac.new(_secret(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(sig, expected):
            return None
        username, expires = payload.decode().rsplit(":", 1)
        if int(expires) < (time.time() if now is None else now):
            return None
        return username
    except (ValueError, UnicodeDecodeError, AuthNotConfigured):
        return None


if __name__ == "__main__":
    # python -m app.auth.security  -> prints a hash to put in .env
    print(_hasher.hash(getpass.getpass("Investigator password: ")))