# Judge checks

## Prototype warning

SilentLine is a fictional-data prototype and is **not for real reports**.
PII removal is not anonymity.

| Check | Evidence |
|---|---|
| App starts | `README.md` local run instructions and `/health` |
| Typed report intake | Browser UI at `/` and `tests/test_report_api.py` |
| Voice/typed fallback | Browser recording control and `/reports/audio` |
| PII removal | `tests/test_scrubber.py` |
| Encrypted storage | `tests/test_case_store.py` |
| Case lookup lockout | `docs/testing-evidence.txt`, `tests/test_cases_api.py` |
| Investigator login | `tests/test_investigator_auth.py`, `tests/test_investigator_routes.py` |
| Protected reports | `/investigator/reports` and `/investigator/reports/{case_id}` |
| Log safety | `tests/test_main.py` and `docs/testing-evidence.txt` |
| CI | `.github/workflows/ci.yml` and `scripts/test.sh` |
| Docker | `Dockerfile` and `docker-compose.yml` |

## Quick demo

1. Run `pip install -r requirements.txt`.
2. Run `uvicorn app.main:app --reload`.
3. Open `http://localhost:8000/`.
4. Submit fictional typed text containing a demo name and phone number.
5. Save the displayed case ID and passphrase, then use Return to a case.
6. Sign in as an investigator and load the scrubbed report list.
