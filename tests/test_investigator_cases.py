import pytest
from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.investigator import router as auth_router
from app.api.investigator_cases import router as cases_router
from app.deps import get_store

USER = "demo-investigator"
PASSWORD = "correct horse battery"

REPORT = {
    "case_id": "C1",
    "category": "fraud",
    "created_date": "2026-11-10",
    "transcript_scrubbed": "Fictional scrubbed report.",
}


class FakeStore:
    def list_cases(self):
        return [{"case_id": "C1", "category": "fraud", "created_date": "2026-11-10"}]

    def get_report_for_investigator(self, case_id):
        return REPORT if case_id == "C1" else None


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SILENTLINE_INVESTIGATOR_USERNAME", USER)
    monkeypatch.setenv("SILENTLINE_INVESTIGATOR_PASSWORD_HASH", PasswordHasher().hash(PASSWORD))
    monkeypatch.setenv("SILENTLINE_AUTH_SECRET", "test-secret-not-for-real-use")
    app = FastAPI()
    app.include_router(auth_router)
    app.include_router(cases_router)
    app.dependency_overrides[get_store] = lambda: FakeStore()
    return TestClient(app)


@pytest.fixture
def headers(client):
    token = client.post(
        "/investigator/login", json={"username": USER, "password": PASSWORD}
    ).json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_list_401_without_login(client):
    assert client.get("/investigator/cases").status_code == 401


def test_detail_401_without_login(client):
    assert client.get("/investigator/cases/C1").status_code == 401


def test_list_with_login(client, headers):
    r = client.get("/investigator/cases", headers=headers)
    assert r.status_code == 200
    assert r.json()[0]["case_id"] == "C1"
    assert "transcript_scrubbed" not in r.json()[0]  # list shows metadata only


def test_detail_with_login(client, headers):
    r = client.get("/investigator/cases/C1", headers=headers)
    assert r.status_code == 200
    assert r.json()["transcript_scrubbed"] == "Fictional scrubbed report."
    assert r.headers["cache-control"] == "no-store"


def test_unknown_case_404(client, headers):
    assert client.get("/investigator/cases/NOPE", headers=headers).status_code == 404


def test_page_loads_and_holds_no_report_data(client):
    r = client.get("/investigator/ui")
    assert r.status_code == 200
    assert "Not for real reports" in r.text
    assert "Fictional scrubbed report." not in r.text