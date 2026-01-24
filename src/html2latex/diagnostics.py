"""Diagnostic event handling for HTML parsing and conversion errors."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Generator, Iterable

    from justhtml.tokens import ParseError

__all__ = [
    "DiagnosticEvent",
    "DiagnosticLocation",
    "DiagnosticsError",
    "collect_errors",
    "diagnostic_context",
    "emit_diagnostic",
    "enforce_strict",
    "extend_diagnostics",
    "from_parse_error",
]


@dataclass(frozen=True, slots=True)
class DiagnosticLocation:
    """Source location information for a diagnostic event."""

    line: int | None = None
    column: int | None = None
    end_column: int | None = None
    node_path: str | None = None


@dataclass(frozen=True, slots=True)
class DiagnosticEvent:
    """A diagnostic event representing an error, warning, or info message."""

    code: str
    category: str
    severity: str
    message: str
    source_html: str | None = None
    location: DiagnosticLocation | None = None
    context: dict[str, Any] = field(default_factory=dict)


class DiagnosticsError(RuntimeError):
    """Exception raised when strict mode encounters diagnostic errors."""

    def __init__(self, events: list[DiagnosticEvent]) -> None:
        message = events[0].message if events else "Diagnostics error"
        super().__init__(message)
        self.events = events

    @property
    def first_error(self) -> DiagnosticEvent | None:
        """Return the first error event, or None if no events."""
        return self.events[0] if self.events else None


_DIAGNOSTIC_SINK: ContextVar[list[DiagnosticEvent] | None] = ContextVar(
    "html2latex_diagnostic_sink", default=None
)


@contextmanager
def diagnostic_context(enabled: bool) -> Generator[list[DiagnosticEvent], None, None]:
    """Context manager for collecting diagnostic events.

    Args:
        enabled: If True, collect diagnostics. If False, yield empty list.

    Yields:
        A list that will be populated with DiagnosticEvent objects.
    """
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
    """Emit a diagnostic event to the current context sink."""
    sink = _DIAGNOSTIC_SINK.get()
    if sink is None:
        return
    sink.append(event)


def extend_diagnostics(events: Iterable[DiagnosticEvent]) -> None:
    """Extend the current context sink with multiple diagnostic events."""
    sink = _DIAGNOSTIC_SINK.get()
    if sink is None:
        return
    sink.extend(events)


def from_parse_error(error: ParseError) -> DiagnosticEvent:
    """Convert a justhtml ParseError to a DiagnosticEvent."""
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
    """Filter diagnostic events to only include errors."""
    return [event for event in events if event.severity == "error"]


def enforce_strict(events: Iterable[DiagnosticEvent]) -> None:
    """Raise DiagnosticsError if any error events are present."""
    errors = collect_errors(events)
    if errors:
        raise DiagnosticsError(errors)
