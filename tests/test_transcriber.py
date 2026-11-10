import io
from types import SimpleNamespace

from app.stt import transcriber


class FakeModel:
    def __init__(self, text="Hello world", language="en", fail=False):
        self.text = text
        self.language = language
        self.fail = fail
        self.got_bytesio = False

    def transcribe(self, audio):
        self.got_bytesio = isinstance(audio, io.BytesIO)
        if self.fail:
            raise RuntimeError("boom")
        return [SimpleNamespace(text=self.text)], SimpleNamespace(language=self.language)


def use(monkeypatch, model):
    monkeypatch.setattr(transcriber, "_get_model", lambda: model)


def test_english_ok(monkeypatch):
    use(monkeypatch, FakeModel("Hello world", "en"))
    r = transcriber.transcribe(b"audio")
    assert (r.text, r.language, r.ok) == ("Hello world", "en", True)


def test_audio_is_passed_in_memory(monkeypatch):
    model = FakeModel()
    use(monkeypatch, model)
    transcriber.transcribe(b"audio")
    assert model.got_bytesio


def test_failure_returns_ok_false(monkeypatch):
    use(monkeypatch, FakeModel(fail=True))
    r = transcriber.transcribe(b"audio")
    assert (r.text, r.language, r.ok) == ("", "unknown", False)


def test_empty_text_returns_ok_false(monkeypatch):
    use(monkeypatch, FakeModel(text="   "))
    assert transcriber.transcribe(b"audio").ok is False


def test_urdu(monkeypatch):
    use(monkeypatch, FakeModel("یہ ایک ٹیسٹ ہے", "ur"))
    assert transcriber.transcribe(b"audio").language == "ur"


def test_urdu_with_english_words_is_mixed(monkeypatch):
    use(monkeypatch, FakeModel("یہ meeting کل ہے project deadline", "ur"))
    assert transcriber.transcribe(b"audio").language == "mixed"


def test_other_language_is_unknown(monkeypatch):
    use(monkeypatch, FakeModel("Bonjour tout le monde", "fr"))
    assert transcriber.transcribe(b"audio").language == "unknown"