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


def _login(client):
    response = client.post("/investigator/login", json={"password": PASSWORD})
    assert response.status_code == 200
    return response.json()["token"]


def test_reports_require_a_token(investigator_client):
    response = investigator_client.get("/investigator/reports")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_single_report_requires_a_token(investigator_client):
    response = investigator_client.get("/investigator/reports/missing")

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


@pytest.mark.parametrize("authorization", ["not-a-bearer", "Bearer invalid.token"])
def test_invalid_authorization_is_rejected(investigator_client, authorization):
    response = investigator_client.get(
        "/investigator/reports", headers={"Authorization": authorization})

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_expired_token_is_rejected(investigator_client):
    now = [1_700_000_000.0]
    auth = InvestigatorAuth(PASSWORD, SECRET, clock=lambda: now[0], ttl_seconds=30)
    app.state.investigator_auth = auth
    token = auth.issue_token()
    now[0] += 31

    response = investigator_client.get(
        "/investigator/reports",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid credentials"}


def test_valid_token_lists_scrubbed_report_metadata(investigator_client, api_store):
    case_id, passphrase = api_store.create_case("Scrubbed investigator report", "safety")
    token = _login(investigator_client)

    response = investigator_client.get(
        "/investigator/reports",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    assert response.json() == [{
        "case_id": case_id,
        "category": "safety",
        "created_date": response.json()[0]["created_date"],
        "transcript_scrubbed": "Scrubbed investigator report",
    }]
    assert passphrase not in response.text


def test_valid_token_reads_one_scrubbed_report(investigator_client, api_store):
    case_id, passphrase = api_store.create_case("Scrubbed investigator report", "safety")
    token = _login(investigator_client)

    response = investigator_client.get(
        f"/investigator/reports/{case_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.json()["transcript_scrubbed"] == "Scrubbed investigator report"
    assert set(response.json()) == {
        "case_id", "category", "created_date", "transcript_scrubbed",
    }
    assert passphrase not in response.text
    assert "passphrase_hash" not in response.text
    assert response.headers["cache-control"] == "no-store"


def test_unknown_report_is_not_found_after_authentication(investigator_client):
    token = _login(investigator_client)

    response = investigator_client.get(
        "/investigator/reports/missing",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Report not found."}
