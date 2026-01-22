"""
HTML → LaTeX conversion entry points.
"""

from __future__ import annotations

from .api import Converter, convert
from .jinja import render_document
from .models import ConvertOptions, LatexDocument

__all__ = [
    "Converter",
    "ConvertOptions",
    "LatexDocument",
    "convert",
    "html2latex",
    "render",
]


def html2latex(html: str | bytes, *, options: ConvertOptions | None = None) -> str:
    """Convert HTML to a LaTeX body fragment."""
    return convert(html, options=options).body


def render(
    html: str | bytes,
    *,
    options: ConvertOptions | None = None,
    template: str | None = None,
) -> str:
    """Render a full LaTeX document using the configured template."""
    doc = convert(html, options=options)
    tmpl = template or (options.template if options else None)
    return render_document(doc.body, preamble=doc.preamble, template=tmpl)
