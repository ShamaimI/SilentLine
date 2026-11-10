"""Local speech-to-text with faster-whisper. Audio stays in memory (BytesIO)."""
import io
import os
import re

from app.contracts import SttResult

MIXED_THRESHOLD = 0.2

_model = None


def _get_model():
    """Load the model once, on first use, then reuse it."""
    global _model
    if _model is None:
        from faster_whisper import WhisperModel

        size = os.environ.get("WHISPER_MODEL", "base")
        _model = WhisperModel(size, device="cpu", compute_type="int8")
    return _model


def _map_language(code: str, text: str) -> str:
    """Map Whisper's single language code to our en/ur/mixed/unknown."""
    words = text.split()
    if not words:
        return "unknown"
    latin = sum(1 for w in words if re.search(r"[A-Za-z]", w))
    arabic = sum(1 for w in words if re.search(r"[\u0600-\u06FF]", w))

    if code == "ur":
        return "mixed" if latin / len(words) >= MIXED_THRESHOLD else "ur"
    if code == "en":
        return "mixed" if arabic / len(words) >= MIXED_THRESHOLD else "en"
    return "unknown"


def transcribe(audio_bytes: bytes) -> SttResult:
    """Audio bytes in, SttResult out. Never raises: failure gives ok=False."""
    try:
        segments, info = _get_model().transcribe(io.BytesIO(audio_bytes))
        text = " ".join(s.text.strip() for s in segments).strip()
    except Exception:
        # Deliberately no logging of the error: it could contain report content.
        return SttResult(text="", language="unknown", ok=False)

    if not text:
        return SttResult(text="", language="unknown", ok=False)
    return SttResult(text=text, language=_map_language(info.language, text), ok=True)