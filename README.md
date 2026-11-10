# SilentLine

> Privacy-first occupational reporting prototype · Demo only, not for real reports

> AI-Powered SE-MAX · CUI Tech Fest FA'26 · Team: <Team Name>

## What it does

SilentLine lets a reporter submit a voice or typed report while minimizing
identifying data. Audio is processed locally, scrubbed for common PII, and
stored only as an encrypted demo report.

## Problem and user

Reporters who need a lower-exposure reporting channel and authorized
investigators reviewing scrubbed fictional reports.

## Live deployment

- **URL / install link:**
- **Platform:**

## Judge quick start (under 5 minutes)

<!-- Exact steps a judge follows to use the product without your laptop. -->

1. Copy `.env.example` to `.env` and set local demo values.
2. Install dependencies with `pip install -r requirements.txt`.
3. Run `uvicorn app.main:app --reload` and open `http://localhost:8000/docs`.

## Test accounts

| Role | Username / email | Password |
|------|------------------|----------|
|      |                  |          |

<!-- Test accounts only. Never real credentials. -->

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

| Name | Role |
|------|------|
| Shumaim | Backend, product, PII scrubber, case security |
| Ayesha | STT, upload hardening, investigator access |
