from html2latex.html_adapter import parse_html


def test_find_and_findall():
    doc = parse_html("<div><p>One</p><p>Two</p></div>")
    root = doc.root
    first = root.find(".//p")
    assert first is not None
    assert first.tag == "p"
    all_p = root.findall(".//p")
    assert [node.tag for node in all_p] == ["p", "p"]


def test_getprevious_getnext():
    doc = parse_html("<div><p>A</p><p>B</p><p>C</p></div>")
    middle = doc.root.findall(".//p")[1]
    assert middle.getprevious().text.strip() == "A"
    assert middle.getnext().text.strip() == "C"


def test_iterchildren_excludes_text():
    doc = parse_html("<div>Hi<span>There</span>Bye</div>")
    div = doc.root.find(".//div")
    children = list(div.iterchildren())
    assert len(children) == 1
    assert children[0].tag == "span"


def test_text_and_tail():
    doc = parse_html("<div>Hello<span>Inner</span>Tail</div>")
    div = doc.root.find(".//div")
    assert div.text.strip() == "Hello"
    span = div.find(".//span")
    assert span.text.strip() == "Inner"
    assert span.tail.strip() == "Tail"
