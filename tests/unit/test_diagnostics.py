import pytest

from html2latex.api import convert
from html2latex.diagnostics import (
    DiagnosticEvent,
    DiagnosticsError,
    collect_errors,
    diagnostic_context,
    emit_diagnostic,
    enforce_strict,
    extend_diagnostics,
)
from html2latex.models import ConvertOptions
from tests.fixtures.harness import get_fixture_case


def test_collects_diagnostics_parse_error():
    options = ConvertOptions(strict=False, fragment=False)
    fixture = get_fixture_case("errors/parse/invalid-attribute")
    doc = convert(fixture.html, options=options)
    assert any(event.code == "missing-attribute-value" for event in doc.diagnostics)


def test_strict_raises_on_parse_error():
    options = ConvertOptions(strict=True, fragment=False)
    fixture = get_fixture_case("errors/parse/invalid-attribute")
    with pytest.raises(DiagnosticsError):
        convert(fixture.html, options=options)


def test_diagnostics_empty_for_valid_html():
    fixture = get_fixture_case("blocks/paragraph/basic")
    doc = convert(fixture.html)
    assert doc.diagnostics == ()


def test_collect_errors_filters_only_errors():
    warn = DiagnosticEvent(code="w1", category="asset", severity="warn", message="warn")
    err = DiagnosticEvent(code="e1", category="parse", severity="error", message="err")
    assert collect_errors([warn, err]) == [err]


def test_enforce_strict_raises_for_errors():
    err = DiagnosticEvent(code="e1", category="parse", severity="error", message="err")
    with pytest.raises(DiagnosticsError):
        enforce_strict([err])


def test_diagnostic_context_disabled_collects_no_events():
    with diagnostic_context(enabled=False) as events:
        emit_diagnostic(DiagnosticEvent(code="w1", category="x", severity="warn", message="msg"))
    assert events == []


def test_emit_diagnostic_appends_with_sink():
    with diagnostic_context(enabled=True) as events:
        emit_diagnostic(DiagnosticEvent(code="w1", category="x", severity="warn", message="msg"))
    assert events and events[0].code == "w1"


def test_emit_and_extend_without_sink_noop():
    emit_diagnostic(DiagnosticEvent(code="w1", category="x", severity="warn", message="msg"))
    extend_diagnostics([DiagnosticEvent(code="w2", category="x", severity="warn", message="msg")])


def test_diagnostics_error_first_error_none():
    err = DiagnosticsError([])
    assert err.first_error is None
