from justhtml.node import Comment, Text

from html2latex.html_adapter import HtmlNode, is_comment, parse_html


def test_html_adapter_navigation():
    doc = parse_html("<div>Lead <span id='s'>Inner</span> tail<p>Para</p></div>")
    div = doc.root.find(".//div")
    assert div is not None
    assert div.tag == "div"
    assert div.text == "Lead "

    span = doc.root.find(".//span")
    assert span.attrib["id"] == "s"
    assert span.tail == " tail"
    assert span.getparent().tag == "div"
    assert span.getnext().tag == "p"
    assert span.getprevious() is None

    found = doc.root.findall(".//div/span")
    assert [node.tag for node in found] == ["span"]

    fallback = doc.root.findall(".//div/span/em")
    assert fallback == []

    span.set("data-test", "1")
    assert span.attrib["data-test"] == "1"

    span.tag = "em"
    assert span.tag == "em"

    html = span.to_html()
    assert "<em" in html


def test_html_adapter_descendants_and_comment():
    doc = parse_html("<div><!-- note --><span>One</span><p>Two</p></div>")
    div = doc.root.find(".//div")
    tags = [node.tag for node in div.iterdescendants()]
    assert tags == ["span", "p"]

    comment = next(
        child
        for child in div._node.children  # noqa: SLF001
        if isinstance(child, Comment)
    )
    assert is_comment(HtmlNode(comment)) is True


def test_html_adapter_text_node_properties():
    doc = parse_html("Lead <span>One</span>")
    text_node = next(
        child
        for child in doc.root._node.children
        if isinstance(child, Text)  # noqa: SLF001
    )
    wrapped = HtmlNode(text_node)
    assert wrapped.tag == ""
    assert wrapped.attrib == {}
    assert wrapped.text == "Lead "
    assert wrapped.tail == ""
    parent = wrapped.getparent()
    assert parent is not None
    assert parent.tag == ""

    spans = doc.root.findall("span")
    assert [node.tag for node in spans] == ["span"]


def test_html_adapter_remove_child():
    doc = parse_html("<div><span>A</span><span>B</span></div>")
    div = doc.root.find(".//div")
    spans = div.findall(".//span")
    div.remove(spans[0])
    html = div.to_html()
    assert "A" not in html
    assert "B" in html


def test_html_adapter_remove_non_element():
    doc = parse_html("Text only")
    root = doc.root
    root.remove(root)
