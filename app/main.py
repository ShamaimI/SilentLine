"""FastAPI entry point for SilentLine."""

from fastapi import FastAPI

from .contracts import process_report

app = FastAPI(
    title="SilentLine",
    description="Privacy-first occupational reporting prototype.",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    """Return a lightweight readiness response."""

    return {"status": "ok"}
