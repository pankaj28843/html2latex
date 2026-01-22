from html2latex.ast import HtmlDocument, HtmlElement, HtmlText
from html2latex.pipeline import normalize_document
from html2latex.pipeline.normalize import _normalize_children


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


def test_normalize_keeps_unknown_nodes():
    sentinel = object()
    normalized = _normalize_children((sentinel,), set(), parent_is_block=True)
    assert normalized == (sentinel,)


def test_normalize_trims_whitespace_around_block_children():
    li = HtmlElement(
        tag="li",
        children=(
            HtmlText(text="  Outer "),
            HtmlElement(tag="ol", children=()),
        ),
    )
    normalized = normalize_document(HtmlDocument(children=(li,)))
    normalized_li = normalized.children[0]
    assert normalized_li.children[0].text == "Outer"


def test_normalize_preserves_space_before_inline_children():
    paragraph = HtmlElement(
        tag="p",
        children=(
            HtmlText(text="Hello "),
            HtmlElement(tag="em", children=(HtmlText(text="world"),)),
        ),
    )
    normalized = normalize_document(HtmlDocument(children=(paragraph,)))
    normalized_paragraph = normalized.children[0]
    assert normalized_paragraph.children[0].text == "Hello "


def test_normalize_preserves_space_between_inline_nodes():
    paragraph = HtmlElement(
        tag="p",
        children=(
            HtmlText(text="Hello"),
            HtmlElement(tag="em", children=(HtmlText(text="world"),)),
            HtmlText(text=" again"),
        ),
    )
    normalized = normalize_document(HtmlDocument(children=(paragraph,)))
    normalized_paragraph = normalized.children[0]
    assert normalized_paragraph.children[0].text == "Hello"
    assert normalized_paragraph.children[2].text == " again"


def test_normalize_trims_trailing_whitespace_in_block():
    paragraph = HtmlElement(
        tag="p",
        children=(
            HtmlText(text="Hello "),
            HtmlElement(tag="em", children=(HtmlText(text="world"),)),
            HtmlText(text="   "),
        ),
    )
    normalized = normalize_document(HtmlDocument(children=(paragraph,)))
    normalized_paragraph = normalized.children[0]
    assert len(normalized_paragraph.children) == 2
    assert normalized_paragraph.children[0].text == "Hello "


def test_normalize_preserves_leading_space_inside_inline_element():
    paragraph = HtmlElement(
        tag="p",
        children=(
            HtmlText(text="Hi"),
            HtmlElement(tag="span", children=(HtmlText(text=" there"),)),
        ),
    )
    normalized = normalize_document(HtmlDocument(children=(paragraph,)))
    normalized_paragraph = normalized.children[0]
    inline_child = normalized_paragraph.children[1]
    assert inline_child.children[0].text == " there"
