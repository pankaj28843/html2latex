from html2latex.ast import HtmlDocument, HtmlElement, HtmlText
from html2latex.rewrite_pipeline import normalize_document


def test_normalize_merges_text_and_collapses_whitespace():
    doc = HtmlDocument(
        children=(
            HtmlText(text="Hello"),
            HtmlText(text="   world"),
            HtmlElement(tag="span", children=(HtmlText(text="!"),)),
        )
    )
    normalized = normalize_document(doc)
    assert normalized.children[0].text == "Hello world"
    assert normalized.children[1].tag == "span"
    assert normalized.children[1].children[0].text == "!"


def test_normalize_drops_whitespace_only_nodes():
    doc = HtmlDocument(children=(HtmlText(text="   \n\t"),))
    normalized = normalize_document(doc)
    assert normalized.children == ()


def test_normalize_preserves_whitespace_tags():
    pre = HtmlElement(tag="pre", children=(HtmlText(text="a\n   b"),))
    doc = HtmlDocument(children=(pre,))
    normalized = normalize_document(doc, preserve_whitespace_tags={"pre"})
    preserved = normalized.children[0].children[0]
    assert preserved.text == "a\n   b"
