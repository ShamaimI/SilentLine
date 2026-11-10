# Design

## Architecture overview

```text
Browser -> FastAPI intake -> local STT -> PII scrubber
         -> scrubbed text -> optional TTS -> encrypted SQLite
         -> authenticated investigator view
```

<!-- Diagram (Mermaid, image or text) and a short explanation. -->

## Components

| Component | Responsibility | Technology |
|-----------|----------------|------------|
| Browser intake | Voice recording and typed fallback | Browser APIs |
| API | Validation and orchestration | FastAPI |
| STT | Local transcription | faster-whisper |
| PII scrubber | Remove common identifiers | Python rules and local names |
| Storage | Encrypted fictional reports | SQLite |

## Data model

## API / interfaces

| Method | Endpoint / interface | Purpose | Auth required |
|--------|----------------------|---------|---------------|
| `process_report(audio_bytes)` | Python interface | Return scrubbed report output | No |
| `GET` | `/health` | Readiness check | No |
| `POST` | `/investigator/login` | Issue a 30-minute investigator token | No |
| `GET` | `/investigator/reports` | List up to 100 scrubbed reports | Investigator token |
| `GET` | `/investigator/reports/{case_id}` | View one scrubbed report | Investigator token |

## Key decisions and tradeoffs

| Decision | Options considered | Chosen | Why | Tradeoff accepted |
|----------|--------------------|--------|-----|-------------------|
|  |  |  |  |  |

## AI components

STT and optional TTS run locally. Unscrubbed content must not be sent to an
external AI service. If STT or TTS fails, the system must preserve a typed
fallback or complete without persona audio.

<!-- What AI does in the product, what code validates, and what happens when AI fails. -->

## Security and privacy

### Threat model

### Data handled

Raw audio is transient processing input. Stored report content is scrubbed
before persistence. Case access uses a random case ID and a hashed passphrase.

### Known limits

Investigator login uses one shared password from the environment and a
30-minute signed token for this prototype. Five failed passwords for the
fixed investigator-login key lock that login from the case/IP limiter for
15 minutes; this is intentionally a simple demo tradeoff rather than a
multi-user identity system.

Investigator report responses expose the case ID, category, date, and scrubbed
transcript only. They never expose passphrases, password hashes, encryption
fields, or raw report content. List responses are capped at the newest 100
reports. If an individual stored row cannot be decrypted, the investigator
list skips that row rather than exposing an error or failing the whole list.
