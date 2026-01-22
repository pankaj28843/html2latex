import pytest

from html2latex.diagnostics import (
    DiagnosticEvent,
    DiagnosticsError,
    collect_errors,
    enforce_strict,
)
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


def test_asset_warning_collects_diagnostic():
    output, diagnostics = html2latex(
        "<p>Before <img src='missing.png'></p>", return_diagnostics=True
    )
    assert "Before" in output
    assert any(
        event.code == "asset/image-io-error" and event.severity == "warn" for event in diagnostics
    )


def test_strict_does_not_raise_on_warning():
    output = html2latex("<p>Before <img src='missing.png'></p>", strict=True)
    assert "Before" in output


def test_collect_errors_filters_only_errors():
    warn = DiagnosticEvent(code="w1", category="asset", severity="warn", message="warn")
    err = DiagnosticEvent(code="e1", category="parse", severity="error", message="err")
    assert collect_errors([warn, err]) == [err]


def test_enforce_strict_raises_for_errors():
    err = DiagnosticEvent(code="e1", category="parse", severity="error", message="err")
    with pytest.raises(DiagnosticsError):
        enforce_strict([err])
