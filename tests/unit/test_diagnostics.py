import pytest

from html2latex.api import convert
from html2latex.diagnostics import (
    DiagnosticEvent,
    DiagnosticsError,
    collect_errors,
    enforce_strict,
)
from html2latex.models import ConvertOptions


def test_collects_diagnostics_parse_error():
    options = ConvertOptions(strict=False, fragment=False)
    doc = convert("<div id=>Hi</div>", options=options)
    assert any(event.code == "missing-attribute-value" for event in doc.diagnostics)


def test_strict_raises_on_parse_error():
    options = ConvertOptions(strict=True, fragment=False)
    with pytest.raises(DiagnosticsError):
        convert("<div id=>Hi</div>", options=options)


def test_diagnostics_empty_for_valid_html():
    doc = convert("<p>Ok</p>")
    assert doc.diagnostics == ()


def test_collect_errors_filters_only_errors():
    warn = DiagnosticEvent(code="w1", category="asset", severity="warn", message="warn")
    err = DiagnosticEvent(code="e1", category="parse", severity="error", message="err")
    assert collect_errors([warn, err]) == [err]


def test_enforce_strict_raises_for_errors():
    err = DiagnosticEvent(code="e1", category="parse", severity="error", message="err")
    with pytest.raises(DiagnosticsError):
        enforce_strict([err])
