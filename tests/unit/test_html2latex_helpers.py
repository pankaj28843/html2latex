from html2latex.html2latex import render
from html2latex.models import ConvertOptions


def test_render_includes_inferred_packages():
    output = render("<a href='https://example.com'>Link</a>")
    assert "\\usepackage{hyperref}" in output


def test_render_uses_metadata_preamble():
    options = ConvertOptions(metadata={"preamble": "\\usepackage{amsmath}"})
    output = render("<p>Math</p>", options=options)
    assert "\\usepackage{amsmath}" in output
