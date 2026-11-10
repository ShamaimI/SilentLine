import pytest

from app.contracts import SttResult
from app.pipeline import TranscriptionFailed, process_report, process_text


def failing_transcribe(_audio):
    return SttResult(text="", language="unknown", ok=False)


def test_failed_stt_raises_transcription_failed():
    with pytest.raises(TranscriptionFailed):
        process_report(b"some audio bytes", transcribe=failing_transcribe)


def test_empty_text_from_stt_raises_transcription_failed():
    def blank(_audio):
        return SttResult(text="   ", language="en", ok=True)

    with pytest.raises(TranscriptionFailed):
        process_report(b"some audio bytes", transcribe=blank)


def test_typed_text_still_works_after_stt_failure():
    result = process_text("Typed report about a fictional incident.")
    assert result.transcript_scrubbed.strip()