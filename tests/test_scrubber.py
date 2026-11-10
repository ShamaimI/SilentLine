import pytest

from app.scrubber.scrubber import ReporterPII, scrub


@pytest.mark.parametrize("cnic", ["35202-1234567-1", "3520212345671"])
def test_reporter_cnic_removed(cnic):
    out, counts = scrub(f"My CNIC is {cnic} ok", ReporterPII(cnic=cnic))
    assert cnic not in out and counts["CNIC"] == 1


@pytest.mark.parametrize("phone", ["03001234567", "0300-1234567", "+92 300 1234567", "+923001234567", "051-1234567"])
def test_reporter_phone_removed(phone):
    out, counts = scrub(f"Call me on {phone} tonight", ReporterPII(phone=phone))
    assert phone not in out and counts["PHONE"] == 1


def test_reporter_email_removed():
    out, _ = scrub(
        "write to fictional.person@example.com please",
        ReporterPII(email="fictional.person@example.com"),
    )
    assert "@" not in out


def test_accused_name_is_preserved():
    out, counts = scrub("My manager Ahmed Khan took the money")
    assert out == "My manager Ahmed Khan took the money"
    assert counts["NAME"] == 0


def test_reporter_name_is_removed_without_cue_word():
    out, counts = scrub("Bilal", ReporterPII(name="Bilal"))

    assert out == "[NAME]"
    assert counts["NAME"] == 1


@pytest.mark.parametrize("phone", ["+92 300 1234567", "0300-1234567"])
def test_reporter_phone_formats_are_removed(phone):
    out, counts = scrub(phone, ReporterPII(phone=phone))

    assert phone not in out
    assert out == "[PHONE]"
    assert counts["PHONE"] == 1


def test_reporter_cnic_with_hyphens_is_removed():
    out, counts = scrub("35202-1234567-1", ReporterPII(cnic="35202-1234567-1"))

    assert out == "[CNIC]"
    assert counts["CNIC"] == 1


def test_reporter_email_is_removed():
    out, counts = scrub(
        "Contact fictional.person@example.com",
        ReporterPII(email="fictional.person@example.com"),
    )

    assert out == "Contact [EMAIL]"
    assert counts["EMAIL"] == 1


def test_cnic_not_mistaken_for_phone():
    _, counts = scrub("ID 35202-1234567-1")
    assert counts["CNIC"] == 0 and counts["PHONE"] == 0


def test_clean_text_untouched():
    text = "The warehouse accounts were altered in March."
    out, counts = scrub(text)
    assert out == text and sum(counts.values()) == 0


def test_reporter_address_and_other_identifier_are_removed():
    out, counts = scrub(
        "I live at House 4, Lahore. My employee code is R-17.",
        ReporterPII(address="House 4, Lahore", other=("R-17",)),
    )
    assert out == "I live at [ADDRESS]. My employee code is [OTHER]."
    assert counts["ADDRESS"] == counts["OTHER"] == 1