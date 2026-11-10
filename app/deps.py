"""Shared dependencies. The case store is built once, from environment settings."""
import os
from functools import lru_cache

from app.cases.store import CaseStore, load_key


@lru_cache(maxsize=1)
def get_store() -> CaseStore:
    """Raises EncryptionKeyError if ENCRYPTION_KEY is missing or invalid."""
    return CaseStore(os.getenv("SILENTLINE_DB", "data/silentline.db"), load_key())