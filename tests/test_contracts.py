import pytest

from app.contracts import ReportResult, process_report


def test_report_result_has_the_shared_output_shape() -> None:
    result = ReportResult(
        transcript_scrubbed="A scrubbed report",
        removed_counts={"email": 1},
        persona_audio=b"audio",
    )

    assert result.transcript_scrubbed == "A scrubbed report"
    assert result.removed_counts == {"email": 1}
    assert result.persona_audio == b"audio"


def test_process_report_rejects_non_bytes_input() -> None:
    with pytest.raises(TypeError, match="audio_bytes must be bytes"):
        process_report("not audio")  # type: ignore[arg-type]


def test_process_report_rejects_empty_input() -> None:
    with pytest.raises(ValueError, match="audio_bytes must not be empty"):
        process_report(b"")
