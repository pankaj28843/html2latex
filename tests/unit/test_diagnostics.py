import pytest

from html2latex.diagnostics import DiagnosticsError
from html2latex.html2latex import html2latex


def test_return_diagnostics_parse_error():
    output, diagnostics = html2latex("<div id=>Hi</div>", return_diagnostics=True)
    assert "Hi" in output
    assert any(event.code == "missing-attribute-value" for event in diagnostics)


def test_strict_raises_on_parse_error():
    with pytest.raises(DiagnosticsError):
        html2latex("<div id=>Hi</div>", strict=True)


def test_return_diagnostics_empty():
    output, diagnostics = html2latex("<p>Ok</p>", return_diagnostics=True)
    assert "Ok" in output
    assert diagnostics == []
