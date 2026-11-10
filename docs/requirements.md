# Requirements

## Problem statement

Tips are an important source of occupational-fraud reports, but reporters may
avoid channels that collect identifying data. SilentLine demonstrates a local,
fictional-data reporting flow that removes common PII before storage.

## Users

Reporters submitting fictional demo concerns and authenticated investigators
reviewing scrubbed reports.

## Functional requirements

| ID | Requirement | Priority (Must / Should / Stretch) | Status |
|----|-------------|------------------------------------|--------|
| FR-01 | Accept typed reports and browser audio with a typed fallback | Must | Implemented |
| FR-02 | Remove reporter-provided CNICs, phones, emails, names, addresses, and other identifiers while preserving accused/evidence text | Must | Implemented |
| FR-03 | Store only scrubbed report text in encrypted SQLite | Must | Implemented |
| FR-04 | Issue random case credentials and rate-limit lookup failures | Must | Implemented |
| FR-05 | Authenticate investigator routes with expiring signed tokens | Must | Implemented |
| FR-06 | Provide a visible prototype warning and privacy limitations | Must | Implemented |
| FR-07 | Provide a browser UI for reporter and investigator flows | Should | Implemented |

## Non-functional requirements

<!-- Every NFR needs a measurable target and a way to measure it. -->

| ID | Category | Requirement | Target | How measured | Result |
|----|----------|-------------|--------|--------------|--------|
| NFR-01 | Security | Reject oversized audio uploads | 10 MB default | Upload API test | Passed |
| NFR-02 | Security | Lock repeated case and login failures | 5 case/login or 10 IP failures | Rate-limit tests | Passed |
| NFR-03 | Privacy | Do not expose credentials in report responses | No passphrase/hash fields | Route/store tests | Passed |
| NFR-04 | Reliability | Complete the automated test suite | 0 failures | `python -m pytest -v` | 121 passed |

## Constraints

- Six-hour prototype timeline.
- Fictional demo data only.
- Local processing; no external AI service for unscrubbed content.
- In-memory limiter state is suitable only for a single-worker demo.

## Assumptions

- Investigator access uses one shared environment password.
- Browser speech recording availability varies by browser and permissions.

## Out of scope

Live phone integration, network anonymity, voice cloning, multi-user roles,
real-world deployment, and production-grade distributed rate limiting.
