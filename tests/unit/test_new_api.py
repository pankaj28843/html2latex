from html2latex.api import Converter, convert
from html2latex.models import ConvertOptions, LatexDocument


def test_convert_options_defaults():
    options = ConvertOptions()
    assert options.strict is True
    assert options.fragment is True
    assert options.template is None
    assert options.metadata == {}


def test_latex_document_defaults():
    doc = LatexDocument(body="hello")
    assert doc.body == "hello"
    assert doc.preamble == ""
    assert doc.packages == ()
    assert doc.diagnostics == ()


def test_converter_with_options_is_immutable():
    converter = Converter()
    updated = converter.with_options(strict=False)
    assert converter.options.strict is True
    assert updated.options.strict is False


def test_converter_convert_returns_document():
    converter = Converter()
    doc = converter.convert("<p>hi</p>")
    assert doc.body == "hi\\par"
    assert converter.diagnostics == doc.diagnostics


def test_convert_helper_returns_document():
    doc = convert("<p>hi</p>")
    assert doc.body == "hi\\par"
