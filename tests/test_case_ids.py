import re

from app.cases.ids import (
    hash_passphrase,
    new_case_id,
    new_passphrase,
    normalize_passphrase,
    verify_passphrase,
)


def test_case_ids_are_long_urlsafe_and_unique():
    ids = {new_case_id() for _ in range(2000)}
    assert len(ids) == 2000
    assert all(len(i) >= 22 and re.fullmatch(r"[A-Za-z0-9_-]+", i) for i in ids)


def test_passphrase_format_and_charset():
    p = new_passphrase()
    assert re.fullmatch(r"[2-9A-HJKMNP-Z]{4}(-[2-9A-HJKMNP-Z]{4}){3}", p)


def test_passphrases_are_unique():
    assert len({new_passphrase() for _ in range(2000)}) == 2000


def test_hash_does_not_contain_plaintext_and_is_salted():
    p = new_passphrase()
    h1, h2 = hash_passphrase(p), hash_passphrase(p)
    assert normalize_passphrase(p) not in h1
    assert h1 != h2  # different salts


def test_verify_correct_and_wrong():
    p = new_passphrase()
    h = hash_passphrase(p)
    assert verify_passphrase(h, p) is True
    assert verify_passphrase(h, new_passphrase()) is False


def test_verify_is_forgiving_about_case_and_dashes():
    h = hash_passphrase("K7QM-2XJP-9TRD-4WHB")
    assert verify_passphrase(h, "k7qm 2xjp 9trd 4whb") is True
    assert verify_passphrase(h, "K7QM2XJP9TRD4WHB") is True


def test_verify_handles_garbage_hash_and_empty_input():
    assert verify_passphrase("not-a-hash", "anything") is False
    assert verify_passphrase("", "") is False
    h = hash_passphrase("K7QM-2XJP-9TRD-4WHB")
    assert verify_passphrase(h, "") is False