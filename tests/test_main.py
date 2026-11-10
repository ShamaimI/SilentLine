import pytest
from cryptography.fernet import Fernet
from fastapi.testclient import TestClient

from app.cases.store import EncryptionKeyError
from app.deps import get_store
from app.main import app


def test_health_endpoint() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_app_refuses_to_start_without_encryption_key(monkeypatch) -> None:
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    get_store.cache_clear()
    with pytest.raises(EncryptionKeyError):
        with TestClient(app):
            pass


def test_app_starts_with_a_valid_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("SILENTLINE_DB", str(tmp_path / "start.db"))
    monkeypatch.setenv("INVESTIGATOR_PASSWORD", "test-investigator-password")
    monkeypatch.setenv("SESSION_SECRET", "t" * 40)
    get_store.cache_clear()
    try:
        with TestClient(app) as client:
            assert client.get("/health").status_code == 200
    finally:
        get_store.cache_clear()