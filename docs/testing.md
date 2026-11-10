# Testing

## Test strategy

Unit tests cover shared contracts and API smoke behavior first. Each owner adds
tests alongside their module before integration.

## How to run tests

```
pytest
```

## Results summary

| Type | Total | Passed | Failed |
|------|-------|--------|--------|
| Unit | 4 | 4 | 0 |
| Integration / API | 1 | 1 | 0 |
| End-to-end / manual |  |  |  |

## Edge cases covered

| ID | Edge case | Expected behaviour | Test / evidence | Result |
|----|-----------|--------------------|-----------------|--------|
| EC-01 | Invalid and empty report input is rejected | Type/value error | `tests/test_contracts.py` | Passed |

## Measured metrics

<!-- Accuracy, response times or other NFR measurements. Report honestly, including weak results. -->

| Metric | Method | Result |
|--------|--------|--------|
|  |  |  |

## Defect log

| ID | Description | Found by / how | Severity | Status | Fix commit |
|----|-------------|----------------|----------|--------|------------|
| D-01 |  |  |  |  |  |

## Known untested areas

STT accuracy, PII removal, encrypted storage, authentication, rate limiting,
upload cleanup, and end-to-end Docker behavior are pending implementation.
