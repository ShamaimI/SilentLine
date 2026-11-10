# Testing

## Test strategy

Unit tests cover contracts, scrubbing, storage, authentication, rate limiting,
and API behavior. The browser page has a route smoke test; manual evidence is
recorded separately.

## How to run tests

```
pytest
```

## Results summary

| Type | Total | Passed | Failed |
|------|-------|--------|--------|
| Automated suite | 121 | 121 | 0 |
| End-to-end / manual | 1 | 1 | 0 |

## Edge cases covered

| ID | Edge case | Expected behaviour | Test / evidence | Result |
|----|-----------|--------------------|-----------------|--------|
| EC-01 | Invalid and empty report input is rejected | Type/value error | `tests/test_contracts.py` | Passed |
| EC-02 | PII formats are scrubbed | Replacement token and count | `tests/test_scrubber.py` | Passed |
| EC-03 | Repeated case/login failures lock out | Generic 429 and Retry-After | `tests/test_ratelimit.py` | Passed |
| EC-04 | Invalid investigator tokens are rejected | Generic 401 | `tests/test_investigator_routes.py` | Passed |
| EC-05 | Unreadable encrypted rows do not break lists | Skip bad row | `tests/test_case_store.py` | Passed |

## Measured metrics

<!-- Accuracy, response times or other NFR measurements. Report honestly, including weak results. -->

| Metric | Method | Result |
|--------|--------|--------|
| Automated suite | `python -m pytest -v` | 121 passed |
| Scrubber suite | `python -m pytest tests/test_scrubber.py -v` | 17 passed |

## Defect log

| ID | Description | Found by / how | Severity | Status | Fix commit |
|----|-------------|----------------|----------|--------|------------|
| D-01 | Unreadable encrypted row caused investigator list failure | Manual test | High | Fixed by skipping row | 575878e |
| D-02 | Access logs could expose request metadata | Review and test | Medium | Fixed by disabling Uvicorn access logger | 1665eff |

## Known untested areas

Measured Urdu/mixed-speech accuracy, temporary-file cleanup for a real
faster-whisper implementation, production deployment, and browser automation
remain untested.
