"""Report submission routes. Audio and raw text stay in memory; never logged."""
import os
from typing import Literal

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.pipeline import TranscriptionFailed, process_report, process_text

router = APIRouter(prefix="/reports", tags=["reports"])

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

Category = Literal[
    "harassment", "academic_dishonesty", "misuse_of_funds",
    "favoritism", "safety", "other",
]


class TextReport(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    category: Category = "other"


class ReportResponse(BaseModel):
    transcript_scrubbed: str
    removed_counts: dict[str, int]
    category: Category = "other"


async def _read_capped(request: Request, limit: int) -> bytes:
    chunks, size = [], 0
    async for chunk in request.stream():
        size += len(chunk)
        if size > limit:
            raise HTTPException(status_code=413, detail="Recording is too large.")
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/text", response_model=ReportResponse)
def submit_text(report: TextReport) -> ReportResponse:
    try:
        result = process_text(report.text)
    except ValueError:
        raise HTTPException(status_code=422, detail="Report text is empty.")
    return ReportResponse(
        transcript_scrubbed=result.transcript_scrubbed,
        removed_counts=result.removed_counts,
        category=report.category,
    )


@router.post("/audio", response_model=ReportResponse)
async def submit_audio(request: Request, category: Category = "other") -> ReportResponse:
    if not request.headers.get("content-type", "").startswith("audio/"):
        raise HTTPException(status_code=415, detail="Send audio as the request body.")
    audio = await _read_capped(request, MAX_UPLOAD_BYTES)
    if not audio:
        raise HTTPException(status_code=400, detail="Empty recording.")
    try:
        result = process_report(audio)
    except TranscriptionFailed:
        raise HTTPException(
            status_code=422,
            detail={"code": "transcription_failed",
                    "message": "We could not transcribe your recording. Please type your report instead."},
        )
    return ReportResponse(
        transcript_scrubbed=result.transcript_scrubbed,
        removed_counts=result.removed_counts,
        category=category,
    )