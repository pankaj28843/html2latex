from html2latex.api import Converter, convert
from html2latex.models import ConvertOptions, LatexDocument
from tests.fixtures.harness import get_fixture_case, normalize_fixture_text


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
    fixture = get_fixture_case("blocks/paragraph/basic")
    doc = converter.convert(fixture.html)
    assert normalize_fixture_text(doc.body) == normalize_fixture_text(fixture.tex)
    assert converter.diagnostics == doc.diagnostics


def test_convert_helper_returns_document():
    fixture = get_fixture_case("blocks/paragraph/basic")
    doc = convert(fixture.html)
    assert normalize_fixture_text(doc.body) == normalize_fixture_text(fixture.tex)
