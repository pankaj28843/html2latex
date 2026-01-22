from __future__ import annotations

from html2latex.ast import HtmlDocument, HtmlElement, HtmlNode, HtmlText
from html2latex.latex import LatexCommand, LatexDocumentAst, LatexGroup, LatexNode, LatexText
from html2latex.styles import StyleConfig

_HEADING_COMMANDS = {
    "h1": "section",
    "h2": "subsection",
    "h3": "subsubsection",
}

_INLINE_COMMANDS = {
    "strong": "textbf",
    "b": "textbf",
    "em": "textit",
    "i": "textit",
    "u": "underline",
}


def convert_document(
    document: HtmlDocument,
    *,
    style: StyleConfig | None = None,
) -> LatexDocumentAst:
    body = _convert_nodes(document.children)
    return LatexDocumentAst(body=body)


def _convert_nodes(nodes: tuple[HtmlNode, ...]) -> tuple[LatexNode, ...]:
    output: list[LatexNode] = []
    for node in nodes:
        output.extend(_convert_node(node))
    return tuple(output)


def _convert_node(node: HtmlNode) -> list[LatexNode]:
    if isinstance(node, HtmlText):
        return [LatexText(text=node.text)]

    if isinstance(node, HtmlElement):
        tag = node.tag.lower()
        if tag in _INLINE_COMMANDS:
            children = _convert_nodes(node.children)
            group = LatexGroup(children=children)
            return [LatexCommand(name=_INLINE_COMMANDS[tag], args=(group,))]

        if tag in _HEADING_COMMANDS:
            children = _convert_nodes(node.children)
            group = LatexGroup(children=children)
            return [LatexCommand(name=_HEADING_COMMANDS[tag], args=(group,))]

        if tag == "br":
            return [LatexCommand(name="newline")]

        if tag in {"p", "div"}:
            children = _convert_nodes(node.children)
            return [*children, LatexCommand(name="par")]

        if tag == "hr":
            return [LatexCommand(name="hrule")]

        children = _convert_nodes(node.children)
        return list(children)

    return []
