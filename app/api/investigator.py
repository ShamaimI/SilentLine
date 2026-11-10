"""Investigator login and the require_investigator dependency."""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.auth.security import (
    TOKEN_TTL_SECONDS,
    AuthNotConfigured,
    check_credentials,
    create_token,
    verify_token,
)

router = APIRouter(prefix="/investigator", tags=["investigator"])
_bearer = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    username: str
    password: str


def require_investigator(
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> str:
    """Use as a dependency on any investigator route. 401 unless logged in."""
    username = verify_token(creds.credentials) if creds else None
    if username is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return username


@router.post("/login")
def login(body: LoginRequest) -> dict:
    try:
        if not check_credentials(body.username, body.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        token = create_token(body.username)
    except AuthNotConfigured:
        raise HTTPException(status_code=503, detail="Investigator login is not configured")
    return {"token": token, "expires_in": TOKEN_TTL_SECONDS}


@router.get("/me")
def me(username: str = Depends(require_investigator)) -> dict:
    return {"username": username}