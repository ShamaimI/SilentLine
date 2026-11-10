"""PII removal. This is PII *removal*, not anonymity."""
import re
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
NAME = re.compile(r"\b(" + "|".join(map(re.escape, _NAMES)) + r")\b", re.IGNORECASE)


def scrub(text: str) -> tuple[str, dict]:
    """Return (scrubbed_text, counts). Order matters: CNIC before phone."""
    counts = {}
    for label, pattern in (("CNIC", CNIC), ("EMAIL", EMAIL), ("PHONE", PHONE), ("NAME", NAME)):
        text, n = pattern.subn(f"[{label}]", text)
        counts[label] = n
    return text, counts