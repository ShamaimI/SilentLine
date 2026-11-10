import pytest
from cryptography.fernet import Fernet

from app.cases.store import CaseStore
from app.deps import get_store
from app.main import app


@pytest.fixture(autouse=True)
def api_store(tmp_path):
    """Every API test gets its own throwaway encrypted store."""
    store = CaseStore(tmp_path / "api_test.db", Fernet.generate_key())
    app.dependency_overrides[get_store] = lambda: store
    yield store
    app.dependency_overrides.clear()