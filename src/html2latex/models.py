"""Data models for html2latex conversion results and configuration."""

from __future__ import annotations

from dataclasses import field
from typing import Any

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from html2latex.diagnostics import DiagnosticEvent


@dataclass(config=ConfigDict(frozen=True))
class ConvertOptions:
    """Configuration options for HTML to LaTeX conversion.

    Attributes:
        strict: If True, raise errors on invalid HTML. If False, emit diagnostics.
        fragment: If True, convert HTML fragment. If False, expect full document.
        formatted: If True, format the output LaTeX with proper indentation.
        template: Optional Jinja2 template name for custom output formatting.
        metadata: Additional metadata to pass to the template.
    """

    strict: bool = True
    fragment: bool = True
    formatted: bool = True
    template: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(config=ConfigDict(frozen=True))
class LatexDocument:
    """Result of HTML to LaTeX conversion.

    Attributes:
        body: The converted LaTeX body content.
        preamble: LaTeX preamble content (package imports, etc.).
        packages: Tuple of required LaTeX package names.
        diagnostics: Tuple of diagnostic events emitted during conversion.
    """

    body: str
    preamble: str = ""
    packages: tuple[str, ...] = ()
    diagnostics: tuple[DiagnosticEvent, ...] = ()
