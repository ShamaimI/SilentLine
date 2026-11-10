"""Investigator auth: one shared password, signed expiring tokens."""
import base64
import hashlib
import hmac
import json
import os
import time
from typing import Callable, Mapping, Optional

MIN_PASSWORD_LEN = 12
MIN_SECRET_LEN = 32


class AuthConfigError(RuntimeError):
    """Raised at startup when investigator auth is not configured safely."""


def _b64e(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64d(text: str) -> bytes:
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class InvestigatorAuth:
    def __init__(self, password: str, secret: str, *,
                 ttl_seconds: int = 30 * 60,
                 clock: Callable[[], float] = time.time) -> None:
        if not isinstance(password, str) or len(password) < MIN_PASSWORD_LEN:
            raise AuthConfigError(
                f"INVESTIGATOR_PASSWORD must be at least {MIN_PASSWORD_LEN} characters")
        if not isinstance(secret, str) or len(secret) < MIN_SECRET_LEN:
            raise AuthConfigError(
                f"SESSION_SECRET must be at least {MIN_SECRET_LEN} characters")
        if ttl_seconds <= 0:
            raise AuthConfigError("ttl_seconds must be positive")
        self._key = secret.encode("utf-8")
        self._ttl = ttl_seconds
        self._clock = clock
        self._password_mac = self._mac(password.encode("utf-8"))

    @property
    def ttl_seconds(self) -> int:
        return self._ttl

    @classmethod
    def from_env(cls, env: Optional[Mapping[str, str]] = None, **kwargs):
        env = os.environ if env is None else env
        password = env.get("INVESTIGATOR_PASSWORD", "")
        secret = env.get("SESSION_SECRET", "")
        encryption_key = env.get("ENCRYPTION_KEY", "")
        if secret and encryption_key and secret == encryption_key:
            raise AuthConfigError("SESSION_SECRET must differ from ENCRYPTION_KEY")
        return cls(password, secret, **kwargs)

    def _mac(self, data: bytes) -> bytes:
        return hmac.new(self._key, data, hashlib.sha256).digest()

    def check_password(self, candidate) -> bool:
        if not isinstance(candidate, str) or not candidate:
            return False
        return hmac.compare_digest(
            self._mac(candidate.encode("utf-8")), self._password_mac)

    def issue_token(self) -> str:
        now = int(self._clock())
        payload = json.dumps(
            {"role": "investigator", "iat": now, "exp": now + self._ttl},
            separators=(",", ":")).encode("utf-8")
        body = _b64e(payload)
        sig = _b64e(self._mac(body.encode("ascii")))
        return f"{body}.{sig}"

    def verify_token(self, token) -> bool:
        try:
            if not isinstance(token, str) or len(token) > 1024:
                return False
            parts = token.split(".")
            if len(parts) != 2:
                return False
            body, sig = parts
            expected = _b64e(self._mac(body.encode("ascii")))
            if not hmac.compare_digest(sig.encode("ascii"), expected.encode("ascii")):
                return False
            data = json.loads(_b64d(body))
            if not isinstance(data, dict) or data.get("role") != "investigator":
                return False
            exp = data.get("exp")
            if isinstance(exp, bool) or not isinstance(exp, (int, float)):
                return False
            return self._clock() < exp
        except (ValueError, TypeError):
            return False