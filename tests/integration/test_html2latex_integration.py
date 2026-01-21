import os

import pytest

import html2latex.html2latex as html2latex_module
from html2latex.html2latex import Table, delegate, html2latex
from html2latex.html_adapter import parse_html


class DummyPopen:
    def __init__(self, *args, **kwargs):  # noqa: ANN001
        self.args = args
        self.kwargs = kwargs

    def wait(self):
        return 0


def test_table_previous_next_flags():
    doc = parse_html("<p>Before</p><table><tbody><tr><td>A</td></tr></tbody></table><p>After</p>")
    table = doc.root.find(".//table")
    assert table is not None
    tbl = Table(table)
    assert tbl.content["has_previous_element"] is True
    assert tbl.content["has_next_element"] is True


def test_table_no_content_render():
    doc = parse_html("<table></table>")
    table = doc.root.find(".//table")
    assert table is not None
    tbl = Table(table)
    assert tbl.has_content is False
    assert tbl.render() == ""


def test_table_colgroup_unknown_width():
    html = (
        "<table><colgroup><col style='height: 10px'></colgroup>"
        "<tbody><tr><td>A</td></tr></tbody></table>"
    )
    output = html2latex(html)
    assert "\\begin{tabular}" in output


def test_table_row_style_width_fallback_invalid():
    html = "<table><tbody><tr><td style='width: bad'>A</td><td>B</td></tr></tbody></table>"
    output = html2latex(html)
    assert "\\begin{tabular}" in output


def test_table_total_width_zero():
    html = (
        "<table><colgroup><col style='width: 0px'><col style='width: 0px'></colgroup>"
        "<tbody><tr><td>A</td><td>B</td></tr></tbody></table>"
    )
    output = html2latex(html)
    assert "\\begin{tabular}" in output


def test_remote_image_download(monkeypatch):
    original_isfile = os.path.isfile
    original_isdir = os.path.isdir
    template_root = os.path.join(
        os.path.dirname(os.path.realpath(html2latex_module.__file__)),
        "templates",
    )

    def _isdir(path):  # noqa: ANN001
        if template_root in path:
            return original_isdir(path)
        return True

    calls = {"count": 0}

    def _isfile(_path):  # noqa: ANN001
        calls["count"] += 1
        if template_root in _path or _path.endswith(".tex"):
            return original_isfile(_path)
        return calls["count"] > 1

    monkeypatch.setattr(html2latex_module.os.path, "isdir", _isdir)
    monkeypatch.setattr(html2latex_module.os.path, "isfile", _isfile)
    monkeypatch.setattr(
        html2latex_module.subprocess,
        "Popen",
        lambda *args, **kwargs: DummyPopen(*args, **kwargs),
    )

    html = "<p>Img <img src='http://example.com/foo.png' style='width:10px;height:20px;'></p>"
    output = html2latex(html)
    assert "\\includegraphics" in output


def test_grayscale_image_conversion(monkeypatch):
    monkeypatch.setattr(html2latex_module.os.path, "isdir", lambda _path: True)
    monkeypatch.setattr(
        html2latex_module.subprocess,
        "Popen",
        lambda *args, **kwargs: DummyPopen(*args, **kwargs),
    )

    html = "<p>Img <img src='local.png' style='width:10px;height:20px;'></p>"
    output = html2latex(html, CONVERT_IMAGE_TO_GRAYSCALE=True)
    assert "\\includegraphics" in output


def test_align_image_center(monkeypatch, tmp_path):
    png = tmp_path / "tiny.png"
    png.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01")
    html = f"<p>Img <img src='{png}' style='width:10px;height:20px;'></p>"
    output = html2latex(html, ALIGN_IMAGE_IN_CENTER=True)
    assert "\\begin{center}" in output


def test_html_line_separator():
    html = "<p>A</p><p>B</p>"
    output = html2latex(html, LINE_SPERATOR="\n")
    assert "\n" in output


def test_html_special_replacements():
    html = "<p>\u2715 and \u2613 and \u03f5</p>"
    output = html2latex(html)
    assert "\\times" in output or "\u00d7" in output
    assert "\\epsilon" in output


def test_fix_encoding_of_html_using_lxml():
    html = "<div>Hi</div>"
    output = html2latex(html)
    assert "Hi" in output


def test_table_render_with_th():
    html = "<table><tr><th>Head</th></tr></table>"
    parsed = parse_html(html)
    th = parsed.root.find(".//th")
    assert th is not None
    output = delegate(th)
    assert "\\textbf{Head}" in output


@pytest.mark.parametrize(
    ("html", "expected"),
    [
        ("<p>foo__bar</p>", "\\underline{\\thickspace}"),
        ("<p>\u009f</p>", ""),
    ],
)
def test_output_normalization_paths(html, expected):
    output = html2latex(html)
    if expected:
        assert expected in output
    else:
        assert "\u009f" not in output
