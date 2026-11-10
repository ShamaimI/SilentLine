# AI Usage Log

Required by the event rules. Log every meaningful use of AI tools during the build.

## Tools used

| Tool | Used for |
|------|----------|
| Copilot SDK in VS Code | Scaffold, implementation, tests, documentation, and review |

## Log

| Time | Member | Tool | What it was asked | What was accepted / changed / rejected | How it was verified |
|------|--------|------|-------------------|----------------------------------------|---------------------|
| 2026-11-10 | Shumaim | Copilot SDK in VS Code | Build SilentLine prototype modules and tests | Accepted implementation after manual review and pytest validation | Full suite and focused tests |

## Reflection

### Where AI helped most

Generating testable security boundaries, route tests, and documentation
reduced setup time during the six-hour prototype.

### Where AI was wrong or misleading

The initial investigator list behavior omitted scrubbed text despite the agreed
response contract; this was caught in review and corrected with a regression
test. Manual evidence claims were not added without observed output.

### What we did not delegate to AI

Final manual demo decisions, fictional data selection, and acceptance of test
results remained with the team.
