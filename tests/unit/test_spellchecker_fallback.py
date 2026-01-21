import pytest

from html2latex.utils import spellchecker


class DummyDict:
    def __init__(self, language):  # noqa: ARG002
        self.valid = {"good", "words"}

    def check(self, word):
        return word in self.valid


class DummyEnchant:
    def Dict(self, language):  # noqa: N802
        return DummyDict(language)


def test_require_enchant_raises(monkeypatch):
    monkeypatch.setattr(spellchecker, "enchant", None)
    with pytest.raises(RuntimeError):
        spellchecker._require_enchant()


def test_spellchecker_with_dummy_enchant(monkeypatch):
    monkeypatch.setattr(spellchecker, "enchant", DummyEnchant())

    checker = spellchecker.get_word_checker("en_US")
    assert checker("good") is False
    assert checker("bad") is True

    incorrect = set(spellchecker.find_incorrect_words("good bad words", checker))
    assert incorrect == {"bad"}

    out = spellchecker.check_spelling("good bad")
    assert "bad" in out
    assert "\\textcolor{red}" in out

    html = "<p>good bad test</p>"
    html_out = spellchecker.check_spelling_in_html(html)
    assert "<strong" in html_out
    assert "bad" in html_out
