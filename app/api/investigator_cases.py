"""Investigator-only case views: the list, one report, and the static page."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi import Path as PathParam
from fastapi.responses import HTMLResponse

from app.api.investigator import require_investigator
from app.cases.store import CaseStore
from app.deps import get_store

router = APIRouter(prefix="/investigator", tags=["investigator"])

_PAGE = Path(__file__).resolve().parent.parent / "ui" / "investigator.html"


@router.get("/ui", response_class=HTMLResponse)
def page() -> str:
    """The page holds no data; the data routes below are what is protected."""
    return _PAGE.read_text(encoding="utf-8")


@router.get("/cases")
def list_cases(
    response: Response,
    _: str = Depends(require_investigator),
    store: CaseStore = Depends(get_store),
) -> list[dict]:
    response.headers["Cache-Control"] = "no-store"
    return store.list_cases()


@router.get("/cases/{case_id}")
def open_case(
    response: Response,
    case_id: str = PathParam(min_length=1, max_length=64),
    _: str = Depends(require_investigator),
    store: CaseStore = Depends(get_store),
) -> dict:
    report = store.get_report_for_investigator(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    response.headers["Cache-Control"] = "no-store"
    return report