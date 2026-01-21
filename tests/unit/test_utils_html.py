import html2latex.utils.html as html_utils


def test_check_if_html_has_text_basic():
    assert html_utils.check_if_html_has_text("") is False
    assert html_utils.check_if_html_has_text("<p>&nbsp;</p>") is False
    assert html_utils.check_if_html_has_text("<p>Hello</p>") is True


def test_check_if_html_has_text_fallback(monkeypatch):
    def boom(self, data):  # noqa: ARG001
        raise RuntimeError("boom")

    monkeypatch.setattr(html_utils._TextExtractor, "feed", boom)
    assert html_utils.check_if_html_has_text("<p>Hi</p>") is True
    assert html_utils.check_if_html_has_text("   ") is False
