import io
import wave

import pytest

from app.stt.validate import MAX_BYTES, InvalidAudio, validate_audio


def make_wav(seconds: int, rate: int = 8000) -> bytes:
    """Build a silent wav in memory, so no audio file is stored in the repo."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(b"\x00\x00" * rate * seconds)
    return buf.getvalue()


def test_valid_short_wav_passes():
    assert validate_audio(make_wav(2)) == "wav"


def test_empty_rejected():
    with pytest.raises(InvalidAudio):
        validate_audio(b"")


def test_non_bytes_raises_type_error():
    with pytest.raises(TypeError):
        validate_audio("not bytes")


def test_oversized_rejected():
    big = b"RIFF\x00\x00\x00\x00WAVE" + b"\x00" * MAX_BYTES
    with pytest.raises(InvalidAudio, match="too large"):
        validate_audio(big)


def test_text_file_renamed_as_audio_rejected():
    with pytest.raises(InvalidAudio):
        validate_audio(b"hello, this is plain text pretending to be audio")


def test_corrupt_wav_rejected():
    # Valid-looking signature, garbage inside
    corrupt = b"RIFF\x00\x00\x00\x00WAVE" + b"garbage" * 50
    with pytest.raises(InvalidAudio):
        validate_audio(corrupt)


def test_three_minute_clip_rejected():
    with pytest.raises(InvalidAudio, match="too long"):
        validate_audio(make_wav(180))