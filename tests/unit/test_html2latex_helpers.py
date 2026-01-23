from html2latex.html2latex import render
from html2latex.models import ConvertOptions
from tests.fixtures.harness import get_fixture_case


def test_render_includes_inferred_packages():
    fixture = get_fixture_case("inline/link/basic")
    output = render(fixture.html)
    assert "\\usepackage{hyperref}" in output


def test_render_uses_metadata_preamble():
    options = ConvertOptions(metadata={"preamble": "\\usepackage{amsmath}"})
    fixture = get_fixture_case("inline/math/span-tex")
    output = render(fixture.html, options=options)
    assert "\\usepackage{amsmath}" in output
