import pytest

from html2latex.adapters.justhtml_adapter import parse_html
from html2latex.diagnostics import DiagnosticsError
from tests.fixtures.harness import get_fixture_case


def test_parse_html_basic_element():
    fixture = get_fixture_case("blocks/paragraph/basic")
    doc, diagnostics = parse_html(fixture.html)
    assert diagnostics == []
    assert doc.children[0].tag == "p"
    assert doc.children[0].children[0].text == "Hello World"


def test_parse_html_ignores_comments():
    fixture = get_fixture_case("blocks/div/comment-child")
    doc, _ = parse_html(fixture.html)
    div = doc.children[0]
    assert div.tag == "div"
    assert len(div.children) == 1
    assert div.children[0].tag == "span"


def test_parse_html_strict_raises_on_errors():
    fixture = get_fixture_case("errors/parse/invalid-attribute")
    with pytest.raises(DiagnosticsError):
        parse_html(fixture.html, strict=True)
