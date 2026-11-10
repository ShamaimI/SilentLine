import dataclasses

import pytest

from app.contracts import ReportResult, SttResult


def test_report_result_has_the_shared_output_shape() -> None:
    result = ReportResult(
        transcript_scrubbed="A scrubbed report",
        removed_counts={"email": 1},
        persona_audio=b"audio",
    )

    assert result.transcript_scrubbed == "A scrubbed report"
    assert result.removed_counts == {"email": 1}
    assert result.persona_audio == b"audio"


def test_report_result_defaults() -> None:
    result = ReportResult(transcript_scrubbed="x")
    assert result.removed_counts == {}
    assert result.persona_audio is None


def test_report_result_is_frozen() -> None:
    result = ReportResult(transcript_scrubbed="x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        result.transcript_scrubbed = "changed"  # type: ignore[misc]


def test_stt_result_defaults() -> None:
    stt = SttResult(text="hello")
    assert stt.language == "unknown"
    assert stt.ok is True