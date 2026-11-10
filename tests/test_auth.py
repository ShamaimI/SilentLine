import pytest
from argon2 import PasswordHasher
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.investigator import router
from app.auth import security

USER = "demo-investigator"
PASSWORD = "correct horse battery"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SILENTLINE_INVESTIGATOR_USERNAME", USER)
    monkeypatch.setenv("SILENTLINE_INVESTIGATOR_PASSWORD_HASH", PasswordHasher().hash(PASSWORD))
    monkeypatch.setenv("SILENTLINE_AUTH_SECRET", "test-secret-not-for-real-use")
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


def login(client, username=USER, password=PASSWORD):
    return client.post("/investigator/login", json={"username": username, "password": password})


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_protected_route_401_without_login(client):
    assert client.get("/investigator/me").status_code == 401


def test_wrong_password_401(client):
    assert login(client, password="wrong").status_code == 401


def test_wrong_username_401(client):
    assert login(client, username="someone-else").status_code == 401


def test_login_then_protected_route_200(client):
    token = login(client).json()["token"]
    r = client.get("/investigator/me", headers=auth(token))
    assert r.status_code == 200
    assert r.json() == {"username": USER}


def test_tampered_token_401(client):
    token = login(client).json()["token"]
    bad = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert client.get("/investigator/me", headers=auth(bad)).status_code == 401


def test_expired_token_401(client):
    old = security.create_token(USER, now=0)  # "issued" in 1970
    assert client.get("/investigator/me", headers=auth(old)).status_code == 401


def test_token_from_other_secret_401(client, monkeypatch):
    token = login(client).json()["token"]
    monkeypatch.setenv("SILENTLINE_AUTH_SECRET", "a-different-secret")
    assert client.get("/investigator/me", headers=auth(token)).status_code == 401


def test_garbage_token_401(client):
    assert client.get("/investigator/me", headers=auth("not-a-token")).status_code == 401


def test_login_503_when_not_configured(client, monkeypatch):
    monkeypatch.delenv("SILENTLINE_INVESTIGATOR_PASSWORD_HASH")
    assert login(client).status_code == 503