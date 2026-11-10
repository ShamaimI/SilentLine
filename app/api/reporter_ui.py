"""Serve the reporter-facing page."""
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(prefix="/reporter", tags=["reporter"])

_PAGE = Path(__file__).resolve().parent.parent / "ui" / "reporter.html"


@router.get("/ui", response_class=HTMLResponse)
def page() -> str:
    return _PAGE.read_text(encoding="utf-8")
