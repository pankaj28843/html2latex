from __future__ import annotations

import re

from html2latex.ast import HtmlDocument, HtmlElement, HtmlNode, HtmlText

_WHITESPACE_RE = re.compile(r"\s+")

_BLOCK_TAGS = {
    "article",
    "aside",
    "blockquote",
    "body",
    "caption",
    "dd",
    "div",
    "dl",
    "dt",
    "figure",
    "figcaption",
    "footer",
    "header",
    "html",
    "hr",
    "li",
    "main",
    "nav",
    "ol",
    "p",
    "pre",
    "section",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "ul",
}


def normalize_document(
    document: HtmlDocument,
    *,
    preserve_whitespace_tags: set[str] | None = None,
) -> HtmlDocument:
    preserve = {tag.lower() for tag in preserve_whitespace_tags or set()}
    children = _normalize_children(document.children, preserve, parent_is_block=True)
    return HtmlDocument(children=children, doctype=document.doctype)


def _normalize_children(
    children: tuple[HtmlNode, ...],
    preserve: set[str],
    parent_is_block: bool,
) -> tuple[HtmlNode, ...]:
    normalized: list[HtmlNode] = []
    buffer: list[str] = []

    def flush_text() -> None:
        if not buffer:
            return
        text = "".join(buffer)
        if text.strip():
            normalized.append(HtmlText(text=text))
        buffer.clear()

    for child in children:
        if isinstance(child, HtmlText):
            collapsed = _collapse_whitespace(child.text)
            if not collapsed.strip():
                continue
            buffer.append(collapsed)
            continue

        if isinstance(child, HtmlElement) and child.tag.lower() in preserve:
            flush_text()
            normalized.append(child)
            continue

        if isinstance(child, HtmlElement):
            flush_text()
            normalized_children = _normalize_children(
                child.children,
                preserve,
                parent_is_block=_is_block_tag(child.tag),
            )
            normalized.append(
                HtmlElement(tag=child.tag, attrs=child.attrs, children=normalized_children)
            )
            continue

        flush_text()
        normalized.append(child)

    flush_text()
    return _trim_boundary_whitespace(tuple(normalized), parent_is_block)


def _trim_boundary_whitespace(
    children: tuple[HtmlNode, ...],
    parent_is_block: bool,
) -> tuple[HtmlNode, ...]:
    if not children or not parent_is_block:
        return children
    trimmed: list[HtmlNode] = []
    last_index = len(children) - 1
    for index, child in enumerate(children):
        if not isinstance(child, HtmlText):
            trimmed.append(child)
            continue
        text = child.text
        if index == 0 or _is_block_element(children[index - 1]):
            text = text.lstrip()
        if index == last_index or _is_block_element(children[index + 1]):
            text = text.rstrip()
        if text.strip():
            trimmed.append(HtmlText(text=text))
    return _trim_boundary_breaks(tuple(trimmed))


def _trim_boundary_breaks(children: tuple[HtmlNode, ...]) -> tuple[HtmlNode, ...]:
    if not children:
        return children
    start = 0
    end = len(children)
    while start < end and _is_line_break(children[start]):
        start += 1
    while end > start and _is_line_break(children[end - 1]):
        end -= 1
    return children[start:end]


def _is_line_break(node: HtmlNode) -> bool:
    return isinstance(node, HtmlElement) and node.tag.lower() == "br"


def _is_block_element(node: HtmlNode) -> bool:
    return isinstance(node, HtmlElement) and node.tag.lower() in _BLOCK_TAGS


def _is_block_tag(tag: str) -> bool:
    return tag.lower() in _BLOCK_TAGS


def _collapse_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text)
