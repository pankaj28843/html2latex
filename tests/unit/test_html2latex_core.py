from html2latex.html2latex import html2latex


def test_html2latex_empty_fragment_returns_empty():
    assert html2latex("   ") == ""


def test_html2latex_math_tex_span():
    output = html2latex("<span class='math-tex'>\\(x+1\\)</span>")
    assert "\\(x+1\\)" in output


def test_html2latex_anchor_without_href():
    output = html2latex("<a>Link</a>")
    assert output.strip() == "Link"


def test_html2latex_anchor_with_href():
    output = html2latex("<a href='https://example.com'>Example</a>")
    assert "\\href{https://example.com}{Example}" in output


def test_html2latex_comment_skipped():
    html = "<p>Hi</p><!-- note --><p>Bye</p>"
    output = html2latex(html)
    assert "note" not in output
    assert "Hi" in output
    assert "Bye" in output


def test_html2latex_list_items_have_spacing():
    output = html2latex("<ul><li>One</li><li>Two</li></ul>")
    assert "\\item One" in output
    assert "\\item Two" in output


def test_html2latex_table_headers_and_colspan():
    html = (
        "<table>"
        "<thead><tr><th>H1</th><th>H2</th></tr></thead>"
        "<tbody><tr><td colspan='2'>Body</td></tr></tbody>"
        "</table>"
    )
    output = html2latex(html)
    assert "\\textbf{H1}" in output
    assert "\\textbf{H2}" in output
    assert "\\multicolumn{2}{l}{Body}" in output
