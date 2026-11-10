import pytest
from fastapi.testclient import TestClient

from app.api import investigator
from app.main import app
from app.security.investigator_auth import InvestigatorAuth


PASSWORD = "correct-horse-battery"
SECRET = "s" * 40


@pytest.fixture
def investigator_client():
    app.state.investigator_auth = InvestigatorAuth(PASSWORD, SECRET)
    investigator.login_limiter = investigator.LookupRateLimiter()
    return TestClient(app)


def test_correct_password_returns_token(investigator_client):
    response = investigator_client.post(
        "/investigator/login", json={"password": PASSWORD})

    assert response.status_code == 200
    assert response.json()["token"]
    assert response.json()["expires_in"] == 1800
    assert PASSWORD not in response.text


def test_wrong_password_returns_generic_401(investigator_client):
    response = investigator_client.post(
        "/investigator/login", json={"password": "wrong-password"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}
    assert PASSWORD not in response.text


def test_five_wrong_passwords_then_lockout(investigator_client):
    for _ in range(5):
        response = investigator_client.post(
            "/investigator/login", json={"password": "wrong-password"})
        assert response.status_code == 401

    response = investigator_client.post(
        "/investigator/login", json={"password": "wrong-password"})
    assert response.status_code == 429
    assert response.headers["retry-after"]
    assert response.json() == {"detail": "Too many attempts. Try again later."}


def test_correct_password_is_blocked_during_lock(investigator_client):
    for _ in range(5):
        investigator_client.post(
            "/investigator/login", json={"password": "wrong-password"})

    response = investigator_client.post(
        "/investigator/login", json={"password": PASSWORD})
    assert response.status_code == 429
    assert PASSWORD not in response.text


@pytest.mark.parametrize("payload", [{}, {"password": ""}, {"password": "x" * 257}])
def test_invalid_password_payload_is_rejected(investigator_client, payload):
    response = investigator_client.post("/investigator/login", json=payload)

    assert response.status_code == 422


def test_login_requires_initialized_auth():
    app.state.investigator_auth = None
    with pytest.raises(RuntimeError, match="not initialized"):
        investigator._get_auth(type("Request", (), {
            "app": type("App", (), {"state": type("State", (), {})()})()
        })())
