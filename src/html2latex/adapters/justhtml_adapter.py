from __future__ import annotations

from typing import Iterable

from justhtml import JustHTML, ParseError
from justhtml.node import Comment, Element, Text

from html2latex.ast import HtmlDocument, HtmlElement, HtmlNode, HtmlText
from html2latex.diagnostics import DiagnosticEvent, enforce_strict, from_parse_error


def parse_html(
    html: str | bytes,
    *,
    fragment: bool = True,
    strict: bool = False,
) -> tuple[HtmlDocument, list[DiagnosticEvent]]:
    document = JustHTML(
        html,
        fragment=fragment,
        safe=False,
        collect_errors=True,
        track_node_locations=False,
    )
    diagnostics = _parse_diagnostics(document.errors)
    if strict:
        enforce_strict(diagnostics)
    children = tuple(_convert_node(child) for child in _iter_children(document.root))
    return HtmlDocument(children=children), diagnostics


def _parse_diagnostics(errors: list[ParseError] | None) -> list[DiagnosticEvent]:
    if not errors:
        return []
    return [from_parse_error(error) for error in errors]


def _iter_children(node) -> Iterable:
    children = getattr(node, "children", None)
    if not children:
        return []
    return [child for child in children if not isinstance(child, Comment)]


def _convert_node(node) -> HtmlNode:
    if isinstance(node, Text):
        return HtmlText(text=node.data or "")
    if isinstance(node, Element):
        attrs = {key: str(value) for key, value in (node.attrs or {}).items()}
        children = tuple(_convert_node(child) for child in _iter_children(node))
        return HtmlElement(tag=node.name or "", attrs=attrs, children=children)
    return HtmlText(text="")
