import html2latex


def test_public_api_exports():
    exported = set(html2latex.__all__)
    assert "convert" in exported
    assert "Converter" in exported
    assert "ConvertOptions" in exported
    assert "LatexDocument" in exported
    assert "html2latex" in exported
    assert "render" in exported


def test_public_api_helpers_work():
    assert html2latex.html2latex("<p>Hi</p>").strip() == "Hi\\par"
