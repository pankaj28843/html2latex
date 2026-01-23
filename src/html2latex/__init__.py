"""html2latex: Convert HTML to LaTeX.

This package provides tools for converting HTML content to LaTeX format,
supporting both simple conversions and full document rendering with templates.

Example usage:
    >>> from html2latex import html2latex
    >>> latex = html2latex("<p>Hello <strong>world</strong></p>")
    >>> print(latex)
    Hello \\textbf{world}\\par

For more control, use the Converter class:
    >>> from html2latex import Converter, ConvertOptions
    >>> converter = Converter(ConvertOptions(strict=False))
    >>> result = converter.convert("<p>Hello</p>")
    >>> print(result.body)
"""

from __future__ import annotations

from .api import Converter, convert
from .html2latex import html2latex, render
from .models import ConvertOptions, LatexDocument

__all__ = [
    "Converter",
    "ConvertOptions",
    "LatexDocument",
    "convert",
    "html2latex",
    "render",
]
