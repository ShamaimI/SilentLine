"""Upload validation for audio. Works on bytes in memory and never writes to disk."""
import io

import av

MAX_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_SECONDS = 120
ALLOWED_FORMATS = {"wav", "mp3", "m4a", "webm", "ogg"}

_REJECT_MSG = "Unsupported or corrupt audio."


class InvalidAudio(Exception):
    """Upload rejected. The message is generic and safe to show to the user."""


def _detect_format(data: bytes):
    """Identify the format from the file's first bytes (its signature)."""
    if data[:4] == b"RIFF" and data[8:12] == b"WAVE":
        return "wav"
    if data[:3] == b"ID3" or (len(data) > 1 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0):
        return "mp3"
    if data[4:8] == b"ftyp":
        return "m4a"
    if data[:4] == b"\x1a\x45\xdf\xa3":
        return "webm"
    if data[:4] == b"OggS":
        return "ogg"
    return None


def _check_audio(data: bytes) -> None:
    """Confirm the bytes decode as audio and are not longer than MAX_SECONDS."""
    try:
        with av.open(io.BytesIO(data)) as container:
            if not container.streams.audio:
                raise InvalidAudio(_REJECT_MSG)

            if container.duration is not None:
                seconds = container.duration / av.time_base
                if seconds > MAX_SECONDS:
                    raise InvalidAudio("Recording is too long.")
                return

            # No length stored in the file (common for browser webm):
            # count while decoding and stop early once the limit is passed.
            seconds = 0.0
            for frame in container.decode(audio=0):
                seconds += frame.samples / frame.sample_rate
                if seconds > MAX_SECONDS:
                    raise InvalidAudio("Recording is too long.")
    except InvalidAudio:
        raise
    except Exception:
        # The decoder raises many kinds of errors on bad files.
        # We never show them to the user.
        raise InvalidAudio(_REJECT_MSG)


def validate_audio(data: bytes) -> str:
    """Return the detected format, or raise InvalidAudio."""
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    if not data:
        raise InvalidAudio("Empty upload.")
    if len(data) > MAX_BYTES:
        raise InvalidAudio("File is too large.")

    fmt = _detect_format(data)
    if fmt is None or fmt not in ALLOWED_FORMATS:
        raise InvalidAudio(_REJECT_MSG)

    _check_audio(data)
    return fmt