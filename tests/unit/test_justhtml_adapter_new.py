import pytest

from html2latex.adapters.justhtml_adapter import parse_html
from html2latex.diagnostics import DiagnosticsError


def test_parse_html_basic_element():
    doc, diagnostics = parse_html("<p>Hello</p>")
    assert diagnostics == []
    assert doc.children[0].tag == "p"
    assert doc.children[0].children[0].text == "Hello"


def test_parse_html_ignores_comments():
    doc, _ = parse_html("<div><!--skip--><span>Hi</span></div>")
    div = doc.children[0]
    assert div.tag == "div"
    assert len(div.children) == 1
    assert div.children[0].tag == "span"


def test_parse_html_strict_raises_on_errors():
    with pytest.raises(DiagnosticsError):
        parse_html("<div id=>Hi</div>", strict=True)
