from __future__ import annotations

from collections.abc import Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any

from justhtml.tokens import ParseError


@dataclass(frozen=True, slots=True)
class DiagnosticLocation:
    line: int | None = None
    column: int | None = None
    end_column: int | None = None
    node_path: str | None = None


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    code: str
    category: str
    severity: str
    message: str
    source_html: str | None = None
    location: DiagnosticLocation | None = None
    context: dict[str, Any] = field(default_factory=dict)


class DiagnosticsError(RuntimeError):
    def __init__(self, events: list[DiagnosticEvent]):
        message = events[0].message if events else "Diagnostics error"
        super().__init__(message)
        self.events = events

    @property
    def first_error(self) -> DiagnosticEvent | None:
        return self.events[0] if self.events else None


_DIAGNOSTIC_SINK: ContextVar[list[DiagnosticEvent] | None] = ContextVar(
    "html2latex_diagnostic_sink", default=None
)


@contextmanager
def diagnostic_context(enabled: bool):
    events: list[DiagnosticEvent] = []
    if not enabled:
        yield events
        return
    token = _DIAGNOSTIC_SINK.set(events)
    try:
        yield events
    finally:
        _DIAGNOSTIC_SINK.reset(token)


def emit_diagnostic(event: DiagnosticEvent) -> None:
    sink = _DIAGNOSTIC_SINK.get()
    if sink is None:
        return
    sink.append(event)


def extend_diagnostics(events: Iterable[DiagnosticEvent]) -> None:
    sink = _DIAGNOSTIC_SINK.get()
    if sink is None:
        return
    sink.extend(events)


def from_parse_error(error: ParseError) -> DiagnosticEvent:
    location = DiagnosticLocation(
        line=error.line,
        column=error.column,
        end_column=getattr(error, "_end_column", None),
    )
    return DiagnosticEvent(
        code=error.code,
        category=error.category or "parse",
        severity="error",
        message=error.message,
        location=location,
    )


def collect_errors(events: Iterable[DiagnosticEvent]) -> list[DiagnosticEvent]:
    return [event for event in events if event.severity == "error"]


def enforce_strict(events: Iterable[DiagnosticEvent]) -> None:
    errors = collect_errors(events)
    if errors:
        raise DiagnosticsError(errors)
