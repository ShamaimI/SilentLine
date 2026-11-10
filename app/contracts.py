"""Shared contracts for the SilentLine report pipeline."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class ReportResult:
    """The scrubbed output returned by report processing."""

    transcript_scrubbed: str
    removed_counts: dict[str, int] = field(default_factory=dict)
    persona_audio: Optional[bytes] = None


def process_report(audio_bytes: bytes) -> ReportResult:
    """Process a report input.

    STT, PII scrubbing, and persona audio are implemented in later phases.
    This explicit contract keeps the integration boundary stable meanwhile.
    """

    if not isinstance(audio_bytes, bytes):
        raise TypeError("audio_bytes must be bytes")
    if not audio_bytes:
        raise ValueError("audio_bytes must not be empty")
    raise NotImplementedError("Report processing is not implemented yet")
