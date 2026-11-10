"""FastAPI entry point for SilentLine."""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from .api.cases import router as cases_router
from .api.investigator import router as investigator_router
from .api.investigator_cases import router as investigator_cases_router
from .api.reports import router as reports_router
from .api.reporter_ui import router as reporter_ui_router
from .deps import get_store
from .security.investigator_auth import InvestigatorAuth
from .web import render_home


@asynccontextmanager
async def lifespan(application: FastAPI):
    logging.getLogger("uvicorn.access").disabled = True
    get_store()  # fail fast: refuse to start without a valid ENCRYPTION_KEY
    application.state.investigator_auth = InvestigatorAuth.from_env()
    yield


app = FastAPI(
    title="SilentLine",
    description="Privacy-first occupational reporting prototype.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(reports_router)
app.include_router(cases_router)
app.include_router(investigator_router)
app.include_router(investigator_cases_router)
app.include_router(reporter_ui_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight readiness response."""

    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def home() -> HTMLResponse:
    return render_home()