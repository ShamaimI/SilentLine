import json

import pytest

from app.security.investigator_auth import (
    AuthConfigError, InvestigatorAuth, _b64e,
)

PASSWORD = "correct-horse-battery"   # test value only
SECRET = "x" * 40
OTHER_SECRET = "y" * 40


class Clock:
    def __init__(self) -> None:
        self.now = 1_700_000_000.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make(**kw):
    clock = Clock()
    return InvestigatorAuth(PASSWORD, SECRET, clock=clock, **kw), clock


def test_from_env_requires_password() -> None:
    with pytest.raises(AuthConfigError):
        InvestigatorAuth.from_env({"SESSION_SECRET": SECRET})


def test_from_env_requires_secret() -> None:
    with pytest.raises(AuthConfigError):
        InvestigatorAuth.from_env({"INVESTIGATOR_PASSWORD": PASSWORD})


def test_rejects_short_password() -> None:
    with pytest.raises(AuthConfigError):
        InvestigatorAuth("short", SECRET)


def test_rejects_short_secret() -> None:
    with pytest.raises(AuthConfigError):
        InvestigatorAuth(PASSWORD, "tooshort")


def test_rejects_secret_equal_to_encryption_key() -> None:
    with pytest.raises(AuthConfigError):
        InvestigatorAuth.from_env({
            "INVESTIGATOR_PASSWORD": PASSWORD,
            "SESSION_SECRET": SECRET,
            "ENCRYPTION_KEY": SECRET,
        })


def test_from_env_ok() -> None:
    auth = InvestigatorAuth.from_env(
        {"INVESTIGATOR_PASSWORD": PASSWORD, "SESSION_SECRET": SECRET})
    assert auth.check_password(PASSWORD)


def test_correct_password_accepted() -> None:
    auth, _ = make()
    assert auth.check_password(PASSWORD)


def test_wrong_password_rejected() -> None:
    auth, _ = make()
    assert not auth.check_password("wrong-password-here")


def test_empty_and_non_string_password_rejected() -> None:
    auth, _ = make()
    assert not auth.check_password("")
    assert not auth.check_password(None)


def test_issued_token_verifies() -> None:
    auth, _ = make()
    assert auth.verify_token(auth.issue_token())


def test_token_expires() -> None:
    auth, clock = make(ttl_seconds=1800)
    token = auth.issue_token()
    clock.advance(1799)
    assert auth.verify_token(token)
    clock.advance(2)
    assert not auth.verify_token(token)


def test_tampered_payload_rejected() -> None:
    auth, clock = make()
    _, sig = auth.issue_token().split(".")
    forged = _b64e(json.dumps(
        {"role": "investigator", "exp": clock() + 10**9}).encode())
    assert not auth.verify_token(f"{forged}.{sig}")


def test_tampered_signature_rejected() -> None:
    auth, _ = make()
    body, sig = auth.issue_token().split(".")
    bad = sig[:-1] + ("A" if sig[-1] != "A" else "B")
    assert not auth.verify_token(f"{body}.{bad}")


def test_token_from_other_secret_rejected() -> None:
    auth, clock = make()
    other = InvestigatorAuth(PASSWORD, OTHER_SECRET, clock=clock)
    assert not auth.verify_token(other.issue_token())


@pytest.mark.parametrize(
    "garbage", ["", "abc", "a.b", "a.b.c", ".", "é.é", None, 12345])
def test_garbage_tokens_rejected(garbage) -> None:
    auth, _ = make()
    assert not auth.verify_token(garbage)


def test_token_contains_no_password() -> None:
    auth, _ = make()
    assert PASSWORD not in auth.issue_token()