"""Shared contracts for the SilentLine report pipeline."""
from dataclasses import dataclass, field
from typing import Literal, Optional

Language = Literal["en", "ur", "mixed", "unknown"]


@dataclass(frozen=True)
class SttResult:
    """What Ayesha's transcriber hands to the pipeline."""
    text: str
    language: Language = "unknown"
    ok: bool = True


@dataclass(frozen=True)
class ReportResult:
    """The scrubbed output returned by report processing."""
    transcript_scrubbed: str
    removed_counts: dict[str, int] = field(default_factory=dict)
    persona_audio: Optional[bytes] = None