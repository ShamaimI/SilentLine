"""Investigator authentication endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.cases.store import CaseStore
from app.deps import get_store
from app.security.investigator_auth import InvestigatorAuth
from app.security.ratelimit import LookupRateLimiter, RateLimitExceeded

router = APIRouter(prefix="/investigator", tags=["investigator"])
login_limiter = LookupRateLimiter()
LOGIN_KEY = "investigator-login"


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class LoginResponse(BaseModel):
    token: str
    expires_in: int


class ReportSummary(BaseModel):
    case_id: str
    category: str
    created_date: str


class ReportView(ReportSummary):
    transcript_scrubbed: str


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _get_auth(request: Request) -> InvestigatorAuth:
    auth = getattr(request.app.state, "investigator_auth", None)
    if not isinstance(auth, InvestigatorAuth):
        raise RuntimeError("investigator authentication is not initialized")
    return auth


def require_investigator(
    request: Request,
    authorization: str | None = Header(default=None),
) -> InvestigatorAuth:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = authorization[7:].strip()
    auth = _get_auth(request)
    if not auth.verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return auth


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request) -> LoginResponse:
    client_ip = _client_ip(request)
    try:
        login_limiter.check(LOGIN_KEY, client_ip)
    except RateLimitExceeded as error:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Try again later.",
            headers={"Retry-After": str(error.retry_after or 900)},
        ) from error

    auth = _get_auth(request)
    if not auth.check_password(body.password):
        login_limiter.record_failure(LOGIN_KEY, client_ip)
        raise HTTPException(status_code=401, detail="Invalid credentials")

    login_limiter.record_success(LOGIN_KEY, client_ip)
    return LoginResponse(token=auth.issue_token(), expires_in=auth.ttl_seconds)


@router.get("/reports", response_model=list[ReportView])
def list_reports(
    response: Response,
    _: InvestigatorAuth = Depends(require_investigator),
    store: CaseStore = Depends(get_store),
) -> list[ReportView]:
    response.headers["Cache-Control"] = "no-store"
    return [ReportView(**report) for report in store.list_cases(limit=100)]


@router.get("/reports/{case_id}", response_model=ReportView)
def get_report(
    case_id: str,
    response: Response,
    _: InvestigatorAuth = Depends(require_investigator),
    store: CaseStore = Depends(get_store),
) -> ReportView:
    report = store.get_report_for_investigator(case_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found.")
    response.headers["Cache-Control"] = "no-store"
    return ReportView(**report)
