"""Reporter lookup: case ID + passphrase. POST (not GET) so credentials never sit in a URL."""
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.cases.store import CaseStore
from app.deps import get_store
from app.security.ratelimit import LookupRateLimiter, RateLimitExceeded

router = APIRouter(prefix="/cases", tags=["cases"])
lookup_limiter = LookupRateLimiter()


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
           request: Request,
           store: CaseStore = Depends(get_store)) -> CaseView:
    client_ip = request.client.host if request.client else "unknown"
    try:
        lookup_limiter.check(body.case_id, client_ip)
    except RateLimitExceeded as error:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(error.retry_after or 900)},
        ) from error

    report = store.get_report(body.case_id, body.passphrase)
    if report is None:
        lookup_limiter.record_failure(body.case_id, client_ip)
        # Same message for unknown ID and wrong passphrase.
        raise HTTPException(status_code=404, detail="Case not found or passphrase incorrect.")
    lookup_limiter.record_success(body.case_id, client_ip)
    response.headers["Cache-Control"] = "no-store"
    return CaseView(**report)