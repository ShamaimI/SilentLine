from fastapi.testclient import TestClient

from app.api import reports
from app.main import app
from app.pipeline import TranscriptionFailed

client = TestClient(app)


def test_text_report_is_scrubbed():
    r = client.post("/reports/text", json={
        "text": "Call Bilal on 03001234567. My name is Shumaim.",
        "category": "harassment",
        "reporter_name": "Shumaim",
    })
    assert r.status_code == 200
    body = r.json()
    assert "Bilal" in body["transcript_scrubbed"]
    assert "Shumaim" not in body["transcript_scrubbed"]
    assert body["category"] == "harassment"


def test_text_report_rejects_empty_and_blank():
    assert client.post("/reports/text", json={"text": ""}).status_code == 422
    assert client.post("/reports/text", json={"text": "   "}).status_code == 422


def test_text_report_rejects_unknown_category():
    r = client.post("/reports/text", json={"text": "hello", "category": "nonsense"})
    assert r.status_code == 422


def test_text_report_rejects_huge_text():
    r = client.post("/reports/text", json={"text": "a" * 20_001})
    assert r.status_code == 422


def test_audio_report_happy_path_uses_scrubber():
    r = client.post("/reports/audio", content=b"fake-audio", headers={"content-type": "audio/webm"})
    assert r.status_code == 200
    assert "transcript_scrubbed" in r.json()


def test_audio_rejects_wrong_content_type():
    r = client.post("/reports/audio", content=b"x", headers={"content-type": "application/json"})
    assert r.status_code == 415


def test_audio_rejects_empty_body():
    r = client.post("/reports/audio", content=b"", headers={"content-type": "audio/webm"})
    assert r.status_code == 400


def test_audio_rejects_oversized_body(monkeypatch):
    monkeypatch.setattr(reports, "MAX_UPLOAD_BYTES", 10)
    r = client.post("/reports/audio", content=b"x" * 11, headers={"content-type": "audio/webm"})
    assert r.status_code == 413


def test_transcription_failure_asks_for_typed_report(monkeypatch):
    def boom(_audio, **_kwargs):
        raise TranscriptionFailed("fail")

    monkeypatch.setattr(reports, "process_report", boom)
    r = client.post("/reports/audio", content=b"fake-audio", headers={"content-type": "audio/webm"})
    assert r.status_code == 422
    assert r.json()["detail"]["code"] == "transcription_failed"