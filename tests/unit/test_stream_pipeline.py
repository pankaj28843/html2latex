from html2latex.ast import HtmlDocument, HtmlElement, HtmlText
from html2latex.latex import serialize_document
from html2latex.pipeline import convert_document, stream_convert


def test_stream_convert_matches_serialized_output():
    doc = HtmlDocument(children=(HtmlElement(tag="p", children=(HtmlText(text="Hi"),)),))
    chunks = list(stream_convert(doc))
    assert "".join(chunks) == serialize_document(convert_document(doc))
    assert len(chunks) >= 2
