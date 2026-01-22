from html2latex.api import convert
from html2latex.html2latex import render
from html2latex.models import ConvertOptions


def test_convert_collects_diagnostics_when_not_strict():
    options = ConvertOptions(strict=False, fragment=False)
    doc = convert("<p>Hi</p>", options=options)
    assert doc.diagnostics


def test_convert_infers_packages():
    doc = convert("<a href='https://example.com'>Link</a><img src='x.png'>")
    assert "hyperref" in doc.packages
    assert "graphicx" in doc.packages


def test_convert_includes_custom_preamble_metadata():
    options = ConvertOptions(metadata={"preamble": "\\usepackage{amsmath}"})
    doc = convert("<p>Math</p>", options=options)
    assert "\\usepackage{amsmath}" in doc.preamble


def test_render_outputs_full_document():
    output = render("<p>Hi</p>")
    assert "\\begin{document}" in output
    assert "Hi\\par" in output
