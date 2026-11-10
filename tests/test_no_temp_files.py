import io
import os
import tempfile
import wave

import pytest

from app.stt import transcriber
from app.stt.validate import validate_audio


def make_wav(seconds: int = 2, rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * rate * seconds)
    return buf.getvalue()


def temp_snapshot() -> set:
    return set(os.listdir(tempfile.gettempdir()))


def test_validation_leaves_no_temp_files():
    audio = make_wav()
    before = temp_snapshot()
    validate_audio(audio)
    assert temp_snapshot() - before == set()


def test_transcription_leaves_no_temp_files(monkeypatch):
    pytest.importorskip("faster_whisper")
    monkeypatch.setenv("WHISPER_MODEL", "tiny")
    monkeypatch.setattr(transcriber, "_model", None)  # force a fresh load

    try:
        transcriber._get_model()
    except Exception:
        pytest.skip("Whisper model not available (no download possible)")

    audio = make_wav()
    before = temp_snapshot()
    result = transcriber.transcribe(audio)
    assert temp_snapshot() - before == set()
    assert isinstance(result.ok, bool)