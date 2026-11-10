"""Case IDs and passphrases. Randomness comes from `secrets` (cryptographically secure)."""
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

# No 0/O/1/I/L so a reporter can copy it down without mistakes. 31 symbols.
_ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_GROUPS, _GROUP_LEN = 4, 4  # 16 symbols ~ 79 bits

_hasher = PasswordHasher()


def new_case_id() -> str:
    """128 bits of randomness, URL-safe (22 characters)."""
    return secrets.token_urlsafe(16)


def new_passphrase() -> str:
    """e.g. 'K7QM-2XJP-9TRD-4WHB'."""
    groups = ("".join(secrets.choice(_ALPHABET) for _ in range(_GROUP_LEN)) for _ in range(_GROUPS))
    return "-".join(groups)


def normalize_passphrase(passphrase: str) -> str:
    """Let reporters type it loosely: any case, with or without dashes/spaces."""
    return "".join(ch for ch in passphrase.upper() if ch.isalnum())


def hash_passphrase(passphrase: str) -> str:
    return _hasher.hash(normalize_passphrase(passphrase))


def verify_passphrase(stored_hash: str, passphrase: str) -> bool:
    """False for a wrong passphrase or a malformed hash; never raises on bad input."""
    try:
        return _hasher.verify(stored_hash, normalize_passphrase(passphrase))
    except (VerificationError, InvalidHashError):
        return False