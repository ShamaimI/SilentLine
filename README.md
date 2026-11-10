# SilentLine

> AI-Powered SE-MAX · CUI Tech Fest FA'26 · Team: Leisure Lads

## What it does

SilentLine lets a reporter submit a voice or typed report while minimizing
identifying data. Reporter-provided PII is scrubbed before encrypted storage,
while accused names and incident evidence in the narrative are preserved.

## Problem and user

Reporters who need a lower-exposure reporting channel and authorized
investigators reviewing scrubbed fictional reports.

## Live deployment

- **URL / install link:** Not deployed; run locally using the instructions below.
- **Platform:** Python 3.11+, FastAPI, and Docker

## Judge quick start (under 5 minutes)

1. Clone this repository.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `uvicorn app.main:app --reload` and open `http://localhost:8000/docs`.

## Test accounts

No test accounts are required for the current prototype scaffold.

## Run locally

### Prerequisites

- Python 3.11+
- Docker (optional)

### Setup

```powershell
pip install -r requirements.txt
```

### Environment variables

See `.env.example`. Do not commit credentials or encryption keys.

### Run

```powershell
uvicorn app.main:app --reload
```

### Run tests

```powershell
pytest
```

## Known limitations

- This is a fictional-data prototype and is not suitable for real reports.
- STT, PII scrubbing, storage, authentication, and investigator workflows are
  being implemented incrementally.
- PII removal is not anonymity; story details may still identify a reporter.

## Documentation

- [Requirements](docs/requirements.md)
- [Design](docs/design.md)
- [Testing](docs/testing.md)
- [AI usage log](docs/ai-usage-log.md)
- [Judge checks](docs/judge-checks.md)

## Team

**Team name:** Leisure Lads

| Name | Registration number | Role |
|------|---------------------|------|
| Shumaim Iftikhar | FA23-BAI-048 | Team leader; backend, product, PII scrubber, and case security |
| Ayesha Khizer | FA23-BAI-009 | STT, upload hardening, and investigator access |
