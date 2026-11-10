"""FastAPI entry point for SilentLine."""

from fastapi import FastAPI

from .api.reports import router as reports_router

app = FastAPI(
    title="SilentLine",
    description="Privacy-first occupational reporting prototype.",
    version="0.1.0",
)

app.include_router(reports_router)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight readiness response."""

    return {"status": "ok"}