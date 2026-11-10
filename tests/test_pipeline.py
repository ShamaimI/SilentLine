import pytest

from app.contracts import SttResult
from app.scrubber.scrubber import ReporterPII
from app.pipeline import TranscriptionFailed, process_report, process_text


def fake_ok(_: bytes) -> SttResult:
    return SttResult(text="Call Bilal on 03001234567", language="en")


def test_process_report_rejects_non_bytes_input() -> None:
    with pytest.raises(TypeError, match="audio_bytes must be bytes"):
        process_report("not audio")  # type: ignore[arg-type]


def test_process_report_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="audio_bytes must not be empty"):
        process_report(b"")


def test_process_report_scrubs_the_transcript() -> None:
    result = process_report(
        b"fake-audio",
        transcribe=fake_ok,
        reporter_pii=ReporterPII(name="Bilal", phone="03001234567"),
    )
    assert "Bilal" not in result.transcript_scrubbed
    assert "03001234567" not in result.transcript_scrubbed
    assert result.removed_counts["NAME"] == 1
    assert result.removed_counts["PHONE"] == 1


def test_process_report_raises_when_stt_not_ok() -> None:
    failed = lambda _: SttResult(text="", language="unknown", ok=False)
    with pytest.raises(TranscriptionFailed):
        process_report(b"fake-audio", transcribe=failed)


def test_process_report_raises_when_stt_returns_blank_text() -> None:
    blank = lambda _: SttResult(text="   ", ok=True)
    with pytest.raises(TranscriptionFailed):
        process_report(b"fake-audio", transcribe=blank)


def test_scrubber_is_always_applied_to_stt_text() -> None:
    seen = []

    def spy(text: str, *_):
        seen.append(text)
        return "[SCRUBBED]", {"NAME": 1}

    result = process_report(b"fake-audio", transcribe=fake_ok, scrub_fn=spy)
    assert seen == ["Call Bilal on 03001234567"]
    assert result.transcript_scrubbed == "[SCRUBBED]"


def test_typed_text_is_scrubbed_too() -> None:
    result = process_text(
        "Email me at fictional.person@example.com",
        reporter_pii=ReporterPII(email="fictional.person@example.com"),
    )
    assert "@" not in result.transcript_scrubbed


def test_process_text_rejects_empty_and_non_str() -> None:
    with pytest.raises(ValueError):
        process_text("   ")
    with pytest.raises(TypeError):
        process_text(123)  # type: ignore[arg-type]