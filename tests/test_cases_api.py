from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

REPORT = "Manager Bilal asked me to change marks. Call 03001234567."


def _submit(category="favoritism"):
    r = client.post("/reports/text", json={"text": REPORT, "category": category})
    assert r.status_code == 200
    return r


def test_submission_returns_case_id_and_passphrase_and_no_cache():
    r = _submit()
    body = r.json()
    assert body["case_id"] and body["passphrase"]
    assert r.headers["cache-control"] == "no-store"


def test_reporter_can_return_with_case_id_and_passphrase():
    body = _submit().json()
    r = client.post("/cases/lookup", json={"case_id": body["case_id"], "passphrase": body["passphrase"]})
    assert r.status_code == 200
    view = r.json()
    assert view["transcript_scrubbed"] == body["transcript_scrubbed"]
    assert view["category"] == "favoritism"
    assert r.headers["cache-control"] == "no-store"


def test_stored_text_is_scrubbed_never_raw(api_store):
    body = _submit().json()
    stored = api_store.get_report_for_investigator(body["case_id"])["transcript_scrubbed"]
    assert "Bilal" not in stored and "03001234567" not in stored
    raw_db = open(api_store._db_path, "rb").read()
    assert b"Bilal" not in raw_db and b"03001234567" not in raw_db


def test_wrong_passphrase_and_unknown_case_get_identical_404():
    body = _submit().json()
    wrong = client.post("/cases/lookup", json={"case_id": body["case_id"], "passphrase": "AAAA-AAAA-AAAA-AAAA"})
    unknown = client.post("/cases/lookup", json={"case_id": "no-such-case", "passphrase": body["passphrase"]})
    assert wrong.status_code == unknown.status_code == 404
    assert wrong.json() == unknown.json()


def test_repeated_wrong_lookups_are_rate_limited():
    body = _submit().json()
    payload = {"case_id": body["case_id"], "passphrase": "wrong-passphrase"}

    responses = [client.post("/cases/lookup", json=payload) for _ in range(6)]

    assert [response.status_code for response in responses[:5]] == [404] * 5
    assert responses[5].status_code == 429
    assert responses[5].headers["retry-after"]
    assert responses[5].json()["detail"] == "Too many attempts. Try again later."


def test_lookup_rejects_missing_empty_and_oversized_fields():
    assert client.post("/cases/lookup", json={}).status_code == 422
    assert client.post("/cases/lookup", json={"case_id": "", "passphrase": "x"}).status_code == 422
    assert client.post("/cases/lookup", json={"case_id": "a" * 65, "passphrase": "x"}).status_code == 422
    assert client.post("/cases/lookup", json={"case_id": "a", "passphrase": "x" * 65}).status_code == 422


def test_audio_submission_also_creates_a_retrievable_case():
    r = client.post("/reports/audio?category=safety", content=b"fake-audio", headers={"content-type": "audio/webm"})
    body = r.json()
    again = client.post("/cases/lookup", json={"case_id": body["case_id"], "passphrase": body["passphrase"]})
    assert again.status_code == 200