from html2latex.api import convert
from html2latex.html2latex import render
from html2latex.models import ConvertOptions
from tests.fixtures.harness import get_fixture_case


def test_convert_collects_diagnostics_when_not_strict():
    options = ConvertOptions(strict=False, fragment=True)
    fixture = get_fixture_case("blocks/paragraph/basic")
    doc = convert(fixture.html, options=options)
    assert doc.diagnostics == ()


def test_convert_infers_packages():
    fixture = get_fixture_case("inline/media/link-image")
    doc = convert(fixture.html)
    assert "hyperref" in doc.packages
    assert "graphicx" in doc.packages


def test_convert_includes_custom_preamble_metadata():
    options = ConvertOptions(metadata={"preamble": "\\usepackage{amsmath}"})
    fixture = get_fixture_case("inline/math/span-tex")
    doc = convert(fixture.html, options=options)
    assert "\\usepackage{amsmath}" in doc.preamble


def test_render_outputs_full_document():
    fixture = get_fixture_case("blocks/paragraph/basic")
    output = render(fixture.html)
    assert "\\begin{document}" in output
    assert "Hello World\\par" in output
