"""Reporter lookup: case ID + passphrase. POST (not GET) so credentials never sit in a URL."""
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field

from app.cases.store import CaseStore
from app.deps import get_store

router = APIRouter(prefix="/cases", tags=["cases"])


class LookupRequest(BaseModel):
    case_id: str = Field(min_length=1, max_length=64)
    passphrase: str = Field(min_length=1, max_length=64)  # cap input so hashing can't be abused


class CaseView(BaseModel):
    case_id: str
    category: str
    created_date: str
    transcript_scrubbed: str


@router.post("/lookup", response_model=CaseView)
def lookup(body: LookupRequest, response: Response,
           store: CaseStore = Depends(get_store)) -> CaseView:
    report = store.get_report(body.case_id, body.passphrase)
    if report is None:
        # Same message for unknown ID and wrong passphrase.
        raise HTTPException(status_code=404, detail="Case not found or passphrase incorrect.")
    response.headers["Cache-Control"] = "no-store"
    return CaseView(**report)