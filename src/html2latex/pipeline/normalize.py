from __future__ import annotations

import re

from html2latex.ast import HtmlDocument, HtmlElement, HtmlNode, HtmlText

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_document(
    document: HtmlDocument,
    *,
    preserve_whitespace_tags: set[str] | None = None,
) -> HtmlDocument:
    preserve = {tag.lower() for tag in preserve_whitespace_tags or set()}
    children = _normalize_children(document.children, preserve)
    return HtmlDocument(children=children, doctype=document.doctype)


def _normalize_children(
    children: tuple[HtmlNode, ...],
    preserve: set[str],
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
            normalized_children = _normalize_children(child.children, preserve)
            normalized.append(
                HtmlElement(tag=child.tag, attrs=child.attrs, children=normalized_children)
            )
            continue

        flush_text()
        normalized.append(child)

    flush_text()
    return tuple(normalized)


def _collapse_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text)
