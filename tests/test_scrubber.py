import pytest

from app.scrubber.scrubber import _NAMES, scrub


def test_names_list_is_loaded():
    assert len(_NAMES) >= 10


@pytest.mark.parametrize("cnic", ["35202-1234567-1", "3520212345671"])
def test_cnic_removed(cnic):
    out, counts = scrub(f"My CNIC is {cnic} ok")
    assert cnic not in out and counts["CNIC"] == 1


@pytest.mark.parametrize("phone", ["03001234567", "0300-1234567", "+92 300 1234567", "+923001234567", "051-1234567"])
def test_phone_removed(phone):
    out, counts = scrub(f"Call me on {phone} tonight")
    assert phone not in out and counts["PHONE"] == 1


def test_email_removed():
    out, _ = scrub("write to fictional.person@example.com please")
    assert "@" not in out


def test_planted_names_removed_case_insensitive():
    out, counts = scrub("My manager ahmed Khan took the money")
    assert "ahmed" not in out.lower() and "khan" not in out.lower() and counts["NAME"] == 2


def test_bare_name_is_removed_without_cue_word():
    out, counts = scrub("Bilal")

    assert out == "[NAME]"
    assert counts["NAME"] == 1


@pytest.mark.parametrize("phone", ["+92 300 1234567", "0300-1234567"])
def test_common_pakistani_phone_formats_are_removed(phone):
    out, counts = scrub(phone)

    assert phone not in out
    assert out == "[PHONE]"
    assert counts["PHONE"] == 1


def test_cnic_with_hyphens_is_removed():
    out, counts = scrub("35202-1234567-1")

    assert out == "[CNIC]"
    assert counts["CNIC"] == 1


def test_email_is_removed():
    out, counts = scrub("Contact fictional.person@example.com")

    assert out == "Contact [EMAIL]"
    assert counts["EMAIL"] == 1


def test_cnic_not_mistaken_for_phone():
    _, counts = scrub("ID 35202-1234567-1")
    assert counts["CNIC"] == 1 and counts["PHONE"] == 0


def test_clean_text_untouched():
    text = "The warehouse accounts were altered in March."
    out, counts = scrub(text)
    assert out == text and sum(counts.values()) == 0