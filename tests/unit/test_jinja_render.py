from html2latex.jinja import render_document


def test_render_document_default_template():
    output = render_document("Hello", preamble="\\usepackage{graphicx}")
    assert "\\documentclass{article}" in output
    assert "\\usepackage{graphicx}" in output
    assert "Hello" in output
    assert "\\end{document}" in output


def test_render_document_custom_template():
    template = "Preamble={{ preamble }} Body={{ body }}"
    output = render_document("Body", preamble="P", template=template)
    assert output == "Preamble=P Body=Body"
