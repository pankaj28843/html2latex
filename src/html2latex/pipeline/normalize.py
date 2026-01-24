"""HTML whitespace normalization pipeline."""

from __future__ import annotations

import re

from html2latex.ast import HtmlDocument, HtmlElement, HtmlNode, HtmlText
from html2latex.tags import BLOCK_TAGS

__all__ = ["normalize_document"]

_WHITESPACE_RE = re.compile(r"\s+")


def normalize_document(
    document: HtmlDocument,
    *,
    preserve_whitespace_tags: set[str] | None = None,
) -> HtmlDocument:
    """Normalize whitespace in an HTML document.

    Collapses consecutive whitespace, trims whitespace around block elements,
    and preserves significant whitespace between inline elements.

    Args:
        document: The HTML document to normalize.
        preserve_whitespace_tags: Set of tag names whose whitespace should be preserved.

    Returns:
        A new HtmlDocument with normalized whitespace.
    """
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

    def flush_text_with_whitespace() -> None:
        """Flush buffer preserving significant whitespace between inline elements."""
        if not buffer:
            return
        text = "".join(buffer)
        if text:
            normalized.append(HtmlText(text=text))
        buffer.clear()

    for index, child in enumerate(children):
        if isinstance(child, HtmlText):
            collapsed = _collapse_whitespace(child.text)
            if not collapsed.strip():
                # Whitespace-only text: preserve if between inline elements
                if collapsed and not parent_is_block:
                    # Inside inline context, keep whitespace
                    buffer.append(collapsed)
                elif collapsed and normalized and index < len(children) - 1:
                    # Check if between two inline elements
                    prev_is_inline = isinstance(normalized[-1], HtmlElement) and not _is_block_tag(
                        normalized[-1].tag
                    )
                    next_child = children[index + 1]
                    next_is_inline = isinstance(next_child, HtmlElement) and not _is_block_tag(
                        next_child.tag
                    )
                    if prev_is_inline and next_is_inline:
                        buffer.append(collapsed)
                continue
            buffer.append(collapsed)
            continue

        if isinstance(child, HtmlElement) and child.tag.lower() in preserve:
            flush_text_with_whitespace()
            normalized.append(child)
            continue

        if isinstance(child, HtmlElement):
            if _is_block_tag(child.tag):
                flush_text()  # Strip whitespace before block
            else:
                flush_text_with_whitespace()  # Keep whitespace before inline
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
        prev_child = children[index - 1] if index > 0 else None
        next_child = children[index + 1] if index < last_index else None
        if index == 0 or (prev_child is not None and _is_block_element(prev_child)):
            text = text.lstrip()
        if index == last_index or (next_child is not None and _is_block_element(next_child)):
            text = text.rstrip()
        # Keep whitespace-only text if between two inline elements
        if text.strip():
            trimmed.append(HtmlText(text=text))
        elif text and prev_child is not None and next_child is not None:
            # Whitespace between two elements - check if both are inline
            prev_is_inline = isinstance(prev_child, HtmlElement) and not _is_block_tag(
                prev_child.tag
            )
            next_is_inline = isinstance(next_child, HtmlElement) and not _is_block_tag(
                next_child.tag
            )
            if prev_is_inline and next_is_inline:
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
    return isinstance(node, HtmlElement) and node.tag.lower() in BLOCK_TAGS


def _is_block_tag(tag: str) -> bool:
    return tag.lower() in BLOCK_TAGS


def _collapse_whitespace(text: str) -> str:
    return _WHITESPACE_RE.sub(" ", text)
