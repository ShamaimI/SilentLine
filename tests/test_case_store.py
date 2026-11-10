import pytest
from cryptography.fernet import Fernet

from app.cases.store import CaseStore, EncryptionKeyError, load_key

SECRET_TEXT = "The accounts office altered the attendance sheet in March."


@pytest.fixture
def key():
    return Fernet.generate_key()


@pytest.fixture
def db_path(tmp_path):
    return tmp_path / "test.db"


@pytest.fixture
def store(db_path, key):
    return CaseStore(db_path, key)


def test_create_and_lookup_roundtrip(store):
    case_id, passphrase = store.create_case(SECRET_TEXT, "misuse_of_funds")
    report = store.get_report(case_id, passphrase)
    assert report["transcript_scrubbed"] == SECRET_TEXT
    assert report["category"] == "misuse_of_funds"


def test_report_text_and_passphrase_are_not_in_database_file(store, db_path):
    case_id, passphrase = store.create_case(SECRET_TEXT)
    raw = db_path.read_bytes()
    assert SECRET_TEXT.encode() not in raw
    assert b"accounts office" not in raw
    assert passphrase.encode() not in raw
    assert passphrase.replace("-", "").encode() not in raw


def test_wrong_passphrase_and_unknown_id_look_the_same(store):
    case_id, passphrase = store.create_case(SECRET_TEXT)
    assert store.get_report(case_id, "AAAA-AAAA-AAAA-AAAA") is None
    assert store.get_report("no-such-case", passphrase) is None


def test_created_date_has_no_time(store):
    case_id, _ = store.create_case(SECRET_TEXT)
    date = store.list_cases()[0]["created_date"]
    assert len(date) == 10 and date.count("-") == 2


def test_list_cases_has_no_report_text(store):
    store.create_case(SECRET_TEXT)
    listing = store.list_cases()
    assert len(listing) == 1
    assert "transcript_scrubbed" not in listing[0]
    assert SECRET_TEXT not in str(listing)


def test_investigator_can_read_without_passphrase(store):
    case_id, _ = store.create_case(SECRET_TEXT)
    assert store.get_report_for_investigator(case_id)["transcript_scrubbed"] == SECRET_TEXT
    assert store.get_report_for_investigator("missing") is None


def test_empty_report_rejected(store):
    with pytest.raises(ValueError):
        store.create_case("   ")


def test_wrong_key_cannot_read_reports(db_path):
    first = CaseStore(db_path, Fernet.generate_key())
    case_id, _ = first.create_case(SECRET_TEXT)
    second = CaseStore(db_path, Fernet.generate_key())
    with pytest.raises(EncryptionKeyError):
        second.get_report_for_investigator(case_id)


def test_load_key_requires_a_valid_key(monkeypatch):
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    with pytest.raises(EncryptionKeyError):
        load_key()
    monkeypatch.setenv("ENCRYPTION_KEY", "not-a-real-key")
    with pytest.raises(EncryptionKeyError):
        load_key()
    good = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", good)
    assert load_key() == good.encode()