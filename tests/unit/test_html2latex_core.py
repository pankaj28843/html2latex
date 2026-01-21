import struct

from justhtml import JustHTML
from justhtml.node import Comment

from html2latex.html2latex import delegate, html2latex
from html2latex.html_adapter import HtmlNode


def _write_png(path, width=2, height=3):
    signature = b"\x89PNG\r\n\x1a\n"
    header = signature + b"\x00\x00\x00\rIHDR" + struct.pack(">LL", width, height)
    path.write_bytes(header + b"extra")


def test_math_tex_span():
    html = "<p><span class='math-tex'>\\( a^2 + b^2 = c^2 \\)</span></p>"
    output = html2latex(html)
    assert "\\begin{math}" in output


def test_empty_html_returns_empty():
    assert html2latex("   ") == ""


def test_html_with_no_text_returns_empty():
    assert html2latex("<img src='missing.png' />") == ""


def test_math_tex_gathered():
    html = "<span class='math-tex'>\\( a\\\\b \\)</span>"
    output = html2latex(html)
    assert "\\begin{gathered}" in output


def test_anchor_without_href():
    output = html2latex("<a>Link</a>")
    assert "\\href{Link}{Link}" in output


def test_anchor_with_href():
    output = html2latex("<a href='https://example.com'>Example</a>")
    assert "\\href{https://example.com}{Example}" in output


def test_comment_skipped():
    html = "<p>Hi</p><!-- note --><p>Bye</p>"
    output = html2latex(html)
    assert "note" not in output
    assert "Hi" in output
    assert "Bye" in output


def test_div_render():
    output = html2latex("<div>Block</div>")
    assert "Block" in output


def test_delegate_comment_node():
    parsed = JustHTML("<!-- note -->", fragment=True, safe=False)
    comment = next(child for child in parsed.root.children if isinstance(child, Comment))
    assert delegate(HtmlNode(comment)) == ""


def test_img_missing_file_returns_empty():
    html = "<p>Before <img src='missing.png'></p>"
    output = html2latex(html)
    assert "Before" in output


def test_img_base64(tmp_path):
    img_path = tmp_path / "tiny.png"
    _write_png(img_path)
    html = f"<p>Img <img src='{img_path}' style='width: 10px; height: 20px;'></p>"
    output = html2latex(html, USE_BASE64_ENCODED_STRING_FOR_IMAGE=True)
    assert "\\begin{filecontents*}" in output
    assert "\\includegraphics" in output


def test_text_alignment_center():
    output = html2latex("<p style='text-align: center;'>Centered</p>")
    assert "\\centering" in output


def test_table_colgroup_widths():
    html = (
        "<table>"
        "<colgroup>"
        "<col style='width: 10px'/>"
        "<col style='width: 20%'/>"
        "</colgroup>"
        "<tbody><tr><td>A</td><td>B</td></tr></tbody>"
        "</table>"
    )
    output = html2latex(html)
    assert "\\begin{tabular}" in output
    assert "A" in output and "B" in output


def test_table_headers_and_colspan():
    html = (
        "<table>"
        "<thead><tr><th>H1</th><th>H2</th></tr></thead>"
        "<tbody><tr><td colspan='2'>Body</td></tr></tbody>"
        "</table>"
    )
    output = html2latex(html)
    assert "H1" in output
    assert "H2" in output
    assert "Body" in output


def test_headings_render():
    html = "<h1>One</h1><h2>Two</h2><h3>Three</h3><h4>Four</h4>"
    output = html2latex(html)
    assert "\\section{One}" in output
    assert "\\subsection{Two}" in output
    assert "\\subsubsection{Three}" in output
    assert "\\paragraph{Four}" in output


def test_spellcheck_hook(monkeypatch):
    def _fake_spell(text):  # noqa: ANN001
        return f"XX{text}XX"

    monkeypatch.setattr("html2latex.html2latex.check_spelling", _fake_spell)
    output = html2latex("<p>hello</p>", do_spellcheck=True)
    assert "XX" in output


def test_sub_sup_conversion():
    html = "<p>H<sub>2</sub>O and x<sup>2</sup></p>"
    output = html2latex(html)
    assert "\\begin{math}H_{2}\\end{math}" in output
    assert "\\begin{math}x^{2}\\end{math}" in output


def test_unknown_tag_uses_not_implemented():
    output = html2latex("<custom>Thing</custom>")
    assert "not yet implemented" in output
