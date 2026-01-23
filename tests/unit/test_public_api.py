import html2latex
from tests.fixtures.harness import get_fixture_case, normalize_fixture_text


def test_public_api_exports():
    exported = set(html2latex.__all__)
    assert "convert" in exported
    assert "Converter" in exported
    assert "ConvertOptions" in exported
    assert "LatexDocument" in exported
    assert "html2latex" in exported
    assert "render" in exported


def test_public_api_helpers_work():
    fixture = get_fixture_case("blocks/paragraph/basic")
    result = html2latex.html2latex(fixture.html)
    assert normalize_fixture_text(result) == normalize_fixture_text(fixture.tex)
