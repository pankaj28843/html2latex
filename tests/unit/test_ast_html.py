from html2latex.ast import HtmlDocument, HtmlElement, HtmlText


def test_html_ast_construction():
    text = HtmlText(text="hello")
    element = HtmlElement(tag="p", attrs={"class": "lead"}, children=(text,))
    doc = HtmlDocument(children=(element,), doctype="html")

    assert doc.doctype == "html"
    assert doc.children[0].tag == "p"
    assert doc.children[0].children[0].text == "hello"
