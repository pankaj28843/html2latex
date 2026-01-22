from __future__ import annotations

from html2latex.ast import HtmlDocument, HtmlElement, HtmlNode, HtmlText
from html2latex.latex import (
    LatexCommand,
    LatexDocumentAst,
    LatexEnvironment,
    LatexGroup,
    LatexNode,
    LatexText,
)
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
    "code": "texttt",
    "sup": "textsuperscript",
    "sub": "textsubscript",
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

        if tag in {"ul", "ol"}:
            env = "itemize" if tag == "ul" else "enumerate"
            items: list[LatexNode] = []
            for child in node.children:
                if isinstance(child, HtmlElement) and child.tag.lower() == "li":
                    items.extend(_convert_list_item(child))
            return [LatexEnvironment(name=env, children=tuple(items))]

        if tag == "dl":
            items = _convert_description_list(node.children)
            return [LatexEnvironment(name="description", children=tuple(items))]

        children = _convert_nodes(node.children)
        return list(children)

    return []


def _convert_list_item(node: HtmlElement) -> list[LatexNode]:
    children = _convert_nodes(node.children)
    return [LatexCommand(name="item"), *children]


def _convert_description_list(children: tuple[HtmlNode, ...]) -> list[LatexNode]:
    items: list[LatexNode] = []
    pending_label: str | None = None

    for child in children:
        if not isinstance(child, HtmlElement):
            continue
        tag = child.tag.lower()
        if tag == "dt":
            pending_label = _extract_text(child).strip() or None
            continue
        if tag == "dd":
            options = (pending_label,) if pending_label else ()
            items.append(LatexCommand(name="item", options=options))
            items.extend(_convert_nodes(child.children))
            pending_label = None

    if pending_label:
        items.append(LatexCommand(name="item", options=(pending_label,)))
    return items


def _extract_text(node: HtmlElement) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, HtmlText):
            parts.append(child.text)
        elif isinstance(child, HtmlElement):
            parts.append(_extract_text(child))
    return "".join(parts)
