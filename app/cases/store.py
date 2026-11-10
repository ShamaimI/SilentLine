"""Encrypted case storage (SQLite + Fernet). Only scrubbed text is ever stored."""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.cases.ids import hash_passphrase, new_case_id, new_passphrase, verify_passphrase

# Burned once at import so lookups for unknown case IDs take about as long as real ones.
_DUMMY_HASH = hash_passphrase("DUMMY-DUMMY-DUMMY-DUMMY")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    case_id TEXT PRIMARY KEY,
    passphrase_hash TEXT NOT NULL,
    category TEXT NOT NULL,
    created_date TEXT NOT NULL,
    report_encrypted BLOB NOT NULL
)
"""


class EncryptionKeyError(RuntimeError):
    """Encryption key missing or invalid."""


def load_key(env_var: str = "ENCRYPTION_KEY") -> bytes:
    raw = os.getenv(env_var, "").strip()
    if not raw:
        raise EncryptionKeyError(
            f"{env_var} is not set. Generate one with: "
            "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\"")
    key = raw.encode()
    try:
        Fernet(key)
    except ValueError as exc:
        raise EncryptionKeyError(f"{env_var} is not a valid Fernet key") from exc
    return key


class CaseStore:
    def __init__(self, db_path: str | Path, key: bytes):
        self._fernet = Fernet(key)
        self._db_path = str(db_path)
        Path(self._db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.execute(_SCHEMA)

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self._db_path)

    def create_case(self, scrubbed_text: str, category: str = "other") -> tuple[str, str]:
        """Returns (case_id, passphrase). The passphrase is shown once and never stored."""
        if not scrubbed_text.strip():
            raise ValueError("scrubbed_text must not be empty")
        case_id, passphrase = new_case_id(), new_passphrase()
        encrypted = self._fernet.encrypt(scrubbed_text.encode("utf-8"))
        # Date only (no time) so a record can't be matched to a specific moment.
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO cases VALUES (?, ?, ?, ?, ?)",
                (case_id, hash_passphrase(passphrase), category, today, encrypted),
            )
        return case_id, passphrase

    def get_report(self, case_id: str, passphrase: str) -> Optional[dict]:
        """Reporter lookup. None for an unknown ID or wrong passphrase (same answer for both)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT passphrase_hash, category, created_date, report_encrypted FROM cases WHERE case_id = ?",
                (case_id,),
            ).fetchone()
        if row is None:
            verify_passphrase(_DUMMY_HASH, passphrase)  # keep timing similar
            return None
        if not verify_passphrase(row[0], passphrase):
            return None
        return self._row_to_report(case_id, row[1], row[2], row[3])

    def list_cases(self, limit: int = 100) -> list[dict]:
        """Return newest investigator reports with scrubbed text only."""
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT case_id, category, created_date, report_encrypted FROM cases "
                "ORDER BY created_date DESC, rowid DESC LIMIT ?",
                (limit,),
            ).fetchall()
        reports = []
        for row in rows:
            try:
                reports.append(self._row_to_report(row[0], row[1], row[2], row[3]))
            except EncryptionKeyError:
                continue
        return reports

    def get_report_for_investigator(self, case_id: str) -> Optional[dict]:
        """Caller must already be authenticated as an investigator."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT category, created_date, report_encrypted FROM cases WHERE case_id = ?",
                (case_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_report(case_id, row[0], row[1], row[2])

    def _row_to_report(self, case_id, category, created_date, encrypted) -> dict:
        try:
            text = self._fernet.decrypt(encrypted).decode("utf-8")
        except InvalidToken as exc:
            raise EncryptionKeyError("Cannot decrypt report: wrong or changed ENCRYPTION_KEY") from exc
        return {"case_id": case_id, "category": category, "created_date": created_date,
                "transcript_scrubbed": text}