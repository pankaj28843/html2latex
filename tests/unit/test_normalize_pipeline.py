from html2latex.ast import HtmlDocument, HtmlElement, HtmlText
from html2latex.pipeline import normalize_document
from html2latex.pipeline.normalize import _normalize_children, _trim_boundary_breaks


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


def test_normalize_trims_whitespace_in_body_container():
    body = HtmlElement(
        tag="body",
        children=(
            HtmlText(text="  Hello "),
            HtmlElement(tag="p", children=(HtmlText(text="World"),)),
        ),
    )
    normalized = normalize_document(HtmlDocument(children=(body,)))
    normalized_body = normalized.children[0]
    assert normalized_body.children[0].text == "Hello"


def test_normalize_trims_boundary_breaks_in_blocks():
    paragraph = HtmlElement(
        tag="p",
        children=(
            HtmlElement(tag="br"),
            HtmlText(text="Hello"),
            HtmlElement(tag="br"),
        ),
    )
    normalized = normalize_document(HtmlDocument(children=(paragraph,)))
    normalized_paragraph = normalized.children[0]
    assert len(normalized_paragraph.children) == 1
    assert normalized_paragraph.children[0].text == "Hello"


def test_trim_boundary_breaks_empty_children():
    assert _trim_boundary_breaks(()) == ()


def test_normalize_preserves_whitespace_in_inline_context():
    """Test that whitespace is preserved inside inline elements (parent_is_block=False)."""
    # When normalizing children of a span (inline), whitespace between text should be kept
    span = HtmlElement(
        tag="span",
        children=(
            HtmlElement(tag="b", children=(HtmlText(text="Bold"),)),
            HtmlText(text=" "),  # This whitespace should be preserved
            HtmlElement(tag="i", children=(HtmlText(text="Italic"),)),
        ),
    )
    paragraph = HtmlElement(tag="p", children=(span,))
    normalized = normalize_document(HtmlDocument(children=(paragraph,)))
    normalized_span = normalized.children[0].children[0]
    # The whitespace between <b> and <i> should be preserved
    assert len(normalized_span.children) == 3
    assert normalized_span.children[1].text == " "
