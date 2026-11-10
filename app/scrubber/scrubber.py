"""PII removal. This is PII *removal*, not anonymity."""
import re
from dataclasses import dataclass, field
from pathlib import Path

CNIC = re.compile(r"(?<!\d)\d{5}-?\d{7}-?\d(?!\d)")
PHONE = re.compile(r"(?<![\d-])(?:\+92|0092|92|0)[\s-]?(?:3\d{2}|\d{2,3})[\s-]?\d{6,7}(?!\d)")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def _load_names() -> list[str]:
    path = Path(__file__).with_name("names.txt")
    return [l.strip().lower() for l in path.read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]


_NAMES = _load_names()
if not _NAMES:
    raise RuntimeError("app/scrubber/names.txt is empty: refusing to run without a names list")
@dataclass(frozen=True)
class ReporterPII:
    """Identifiers explicitly provided as belonging to the reporter."""

    name: str | None = None
    cnic: str | None = None
    phone: str | None = None
    email: str | None = None
    address: str | None = None
    other: tuple[str, ...] = field(default_factory=tuple)


def scrub(text: str, reporter_pii: ReporterPII | None = None) -> tuple[str, dict]:
    """Scrub only identifiers explicitly belonging to the reporter."""
    if not isinstance(text, str):
        raise TypeError("text must be str")
    pii = reporter_pii or ReporterPII()
    counts = {"CNIC": 0, "EMAIL": 0, "PHONE": 0, "NAME": 0, "ADDRESS": 0, "OTHER": 0}
    values = (
        ("NAME", pii.name),
        ("CNIC", pii.cnic),
        ("PHONE", pii.phone),
        ("EMAIL", pii.email),
        ("ADDRESS", pii.address),
    )
    for label, value in values:
        if value and value.strip():
            text, n = re.subn(re.escape(value.strip()), f"[{label}]", text, flags=re.IGNORECASE)
            counts[label] += n
    for value in pii.other:
        if value and value.strip():
            text, n = re.subn(re.escape(value.strip()), "[OTHER]", text, flags=re.IGNORECASE)
            counts["OTHER"] += n
    return text, counts