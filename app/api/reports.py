"""Report submission routes. Audio and raw text stay in memory; never logged."""
import os
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from app.cases.store import CaseStore
from app.deps import get_store
from app.pipeline import TranscriptionFailed, process_report, process_text
from app.scrubber.scrubber import ReporterPII

router = APIRouter(prefix="/reports", tags=["reports"])

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_MB", "10")) * 1024 * 1024

Category = Literal[
    "harassment", "academic_dishonesty", "misuse_of_funds",
    "favoritism", "safety", "other",
]


class TextReport(BaseModel):
    text: str = Field(min_length=1, max_length=20_000)
    category: Category = "other"
    reporter_name: str | None = Field(default=None, max_length=200)
    reporter_cnic: str | None = Field(default=None, max_length=32)
    reporter_phone: str | None = Field(default=None, max_length=32)
    reporter_email: str | None = Field(default=None, max_length=320)
    reporter_address: str | None = Field(default=None, max_length=500)


class ReportResponse(BaseModel):
    case_id: str
    passphrase: str  # shown once; only a hash is stored
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


def _save_and_respond(store: CaseStore, result, category: str, response: Response) -> ReportResponse:
    case_id, passphrase = store.create_case(result.transcript_scrubbed, category)
    response.headers["Cache-Control"] = "no-store"  # the passphrase must not be cached
    return ReportResponse(
        case_id=case_id,
        passphrase=passphrase,
        transcript_scrubbed=result.transcript_scrubbed,
        removed_counts=result.removed_counts,
        category=category,
    )


@router.post("/text", response_model=ReportResponse)
def submit_text(report: TextReport, response: Response,
                store: CaseStore = Depends(get_store)) -> ReportResponse:
    try:
        result = process_text(report.text, reporter_pii=ReporterPII(
            name=report.reporter_name,
            cnic=report.reporter_cnic,
            phone=report.reporter_phone,
            email=report.reporter_email,
            address=report.reporter_address,
        ))
    except ValueError:
        raise HTTPException(status_code=422, detail="Report text is empty.")
    return _save_and_respond(store, result, report.category, response)


@router.post("/audio", response_model=ReportResponse)
async def submit_audio(request: Request, response: Response, category: Category = "other",
                       reporter_name: str | None = Query(default=None, max_length=200),
                       reporter_cnic: str | None = Query(default=None, max_length=32),
                       reporter_phone: str | None = Query(default=None, max_length=32),
                       reporter_email: str | None = Query(default=None, max_length=320),
                       reporter_address: str | None = Query(default=None, max_length=500),
                       store: CaseStore = Depends(get_store)) -> ReportResponse:
    if not request.headers.get("content-type", "").startswith("audio/"):
        raise HTTPException(status_code=415, detail="Send audio as the request body.")
    audio = await _read_capped(request, MAX_UPLOAD_BYTES)
    if not audio:
        raise HTTPException(status_code=400, detail="Empty recording.")
    try:
        result = process_report(audio, reporter_pii=ReporterPII(
            name=reporter_name,
            cnic=reporter_cnic,
            phone=reporter_phone,
            email=reporter_email,
            address=reporter_address,
        ))
    except TranscriptionFailed:
        raise HTTPException(
            status_code=422,
            detail={"code": "transcription_failed",
                    "message": "We could not transcribe your recording. Please type your report instead."},
        )
    return _save_and_respond(store, result, category, response)