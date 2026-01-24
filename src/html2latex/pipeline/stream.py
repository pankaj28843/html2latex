"""Streaming HTML to LaTeX conversion."""

from __future__ import annotations

from typing import TYPE_CHECKING

from html2latex.latex import serialize_nodes

from .convert import convert_document

if TYPE_CHECKING:
    from collections.abc import Iterable

    from html2latex.ast import HtmlDocument

__all__ = ["stream_convert"]


def stream_convert(document: HtmlDocument) -> Iterable[str]:
    """Stream-convert an HTML document to LaTeX strings.

    Args:
        document: The HTML document to convert.

    Yields:
        LaTeX string fragments.
    """
    ast = convert_document(document)
    yield from serialize_nodes(ast.body)
