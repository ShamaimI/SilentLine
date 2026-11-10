"""Report pipeline: audio -> STT -> scrub -> result. Audio stays in memory."""
from typing import Callable

from app.contracts import ReportResult, SttResult
from app.scrubber.scrubber import scrub


class TranscriptionFailed(Exception):
    """STT produced no usable text; the caller should offer typed input."""


def _stub_transcribe(audio_bytes: bytes) -> SttResult:
    # Replace with Ayesha's faster-whisper transcriber (app/stt/transcriber.py)
    return SttResult(text="Fictional demo report.", language="en")


def process_text(text: str, scrub_fn: Callable = scrub) -> ReportResult:
    """Typed reports and the STT fallback both come through here."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    if not text.strip():
        raise ValueError("text must not be empty")
    clean, counts = scrub_fn(text)
    return ReportResult(transcript_scrubbed=clean, removed_counts=counts)


def process_report(audio_bytes: bytes,
                   transcribe: Callable[[bytes], SttResult] = _stub_transcribe,
                   scrub_fn: Callable = scrub) -> ReportResult:
    if not isinstance(audio_bytes, bytes):
        raise TypeError("audio_bytes must be bytes")
    if not audio_bytes:
        raise ValueError("audio_bytes must not be empty")
    stt = transcribe(audio_bytes)
    if not stt.ok or not stt.text.strip():
        raise TranscriptionFailed("transcription failed")
    return process_text(stt.text, scrub_fn)