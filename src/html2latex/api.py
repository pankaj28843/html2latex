"""Core API for HTML to LaTeX conversion.

This module provides the Converter class and convert() function for transforming
HTML content into LaTeX. The conversion process includes:
1. HTML parsing with error recovery
2. AST normalization (whitespace handling)
3. Conversion to LaTeX AST
4. Serialization to LaTeX string

For simple usage, use the convert() function. For more control over the
conversion process, instantiate a Converter with ConvertOptions.
"""

from __future__ import annotations

from dataclasses import replace

from .adapters.justhtml_adapter import parse_html
from .diagnostics import diagnostic_context, enforce_strict, extend_diagnostics
from .latex import infer_packages, serialize_document
from .models import ConvertOptions, LatexDocument
from .pipeline import convert_document, normalize_document

__all__ = [
    "Converter",
    "convert",
]


class Converter:
    """Stateful HTML to LaTeX converter with configurable options.

    The Converter class provides a reusable converter instance that maintains
    diagnostics from the last conversion. Use with_options() to create a new
    converter with modified settings.

    Attributes:
        options: The ConvertOptions used for conversion.
        diagnostics: Tuple of DiagnosticEvent from the last conversion.
    """

    def __init__(self, options: ConvertOptions | None = None) -> None:
        """Initialize a new Converter with the given options.

        Args:
            options: Conversion options. If None, uses default ConvertOptions.
        """
        self.options = options or ConvertOptions()
        self.diagnostics: tuple = ()

    def convert(self, html: str | bytes) -> LatexDocument:
        """Convert HTML to a LatexDocument.

        Args:
            html: HTML content as string or bytes.

        Returns:
            LatexDocument containing the converted body, preamble, packages,
            and any diagnostics emitted during conversion.

        Raises:
            DiagnosticsError: If strict mode is enabled and errors are found.
        """
        with diagnostic_context(enabled=True) as events:
            document, parse_events = parse_html(
                html,
                fragment=self.options.fragment,
                strict=False,
            )
            extend_diagnostics(parse_events)
            normalized = normalize_document(document, preserve_whitespace_tags={"pre"})
            latex_ast = convert_document(normalized)
            body = serialize_document(latex_ast, formatted=self.options.formatted)
            packages = tuple(sorted(infer_packages(latex_ast)))
            preamble = _build_preamble(packages, self.options.metadata)
            if self.options.strict:
                enforce_strict(events)
            result = LatexDocument(
                body=body,
                preamble=preamble,
                packages=packages,
                diagnostics=tuple(events),
            )
        self.diagnostics = result.diagnostics
        return result

    def with_options(self, **changes: object) -> Converter:
        """Create a new Converter with modified options.

        Args:
            **changes: Option attributes to override.

        Returns:
            New Converter instance with updated options.
        """
        options = replace(self.options, **changes)
        return Converter(options=options)


def convert(html: str | bytes, *, options: ConvertOptions | None = None) -> LatexDocument:
    """Convert HTML to a LatexDocument.

    This is a convenience function that creates a Converter and performs the
    conversion in one step. For multiple conversions with the same options,
    prefer creating a Converter instance directly.

    Args:
        html: HTML content as string or bytes.
        options: Conversion options. If None, uses default ConvertOptions.

    Returns:
        LatexDocument containing the converted body, preamble, packages,
        and any diagnostics emitted during conversion.

    Raises:
        DiagnosticsError: If strict mode is enabled and errors are found.
    """
    converter = Converter(options=options)
    return converter.convert(html)


def _build_preamble(packages: tuple[str, ...], metadata: dict[str, object]) -> str:
    lines = [f"\\usepackage{{{package}}}" for package in packages]
    extra = metadata.get("preamble")
    if extra:
        lines.append(str(extra))
    return "\n".join(lines)
