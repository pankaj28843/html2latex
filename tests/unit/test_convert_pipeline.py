from html2latex.ast import HtmlDocument, HtmlElement, HtmlText
from html2latex.latex import LatexCommand, LatexText
from html2latex.rewrite_pipeline import convert_document


def test_convert_paragraph_and_inline():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="p",
                children=(
                    HtmlText(text="Hello "),
                    HtmlElement(tag="strong", children=(HtmlText(text="World"),)),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexText)
    assert latex.body[0].text == "Hello "
    assert isinstance(latex.body[1], LatexCommand)
    assert latex.body[1].name == "textbf"
    assert isinstance(latex.body[2], LatexCommand)
    assert latex.body[2].name == "par"


def test_convert_heading():
    doc = HtmlDocument(children=(HtmlElement(tag="h1", children=(HtmlText(text="Title"),)),))
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexCommand)
    assert latex.body[0].name == "section"
