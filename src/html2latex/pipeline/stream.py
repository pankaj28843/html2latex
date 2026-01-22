from __future__ import annotations

from collections.abc import Iterable

from html2latex.ast import HtmlDocument
from html2latex.latex import serialize_nodes

from .convert import convert_document


def stream_convert(document: HtmlDocument) -> Iterable[str]:
    ast = convert_document(document)
    yield from serialize_nodes(ast.body)
