"""
justhtml adapter spike.

This module is not wired into the main conversion flow yet. It provides a
minimal wrapper to align justhtml-style nodes with the subset of lxml APIs
used in the current codebase.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

try:
    from justhtml import JustHTML
except Exception:  # pragma: no cover - optional dependency in this spike
    JustHTML = None


@dataclass
class HtmlDocument:
    root: "HtmlNode"


def parse_html(html: str) -> HtmlDocument:
    if JustHTML is None:
        raise ImportError("justhtml is not installed")
    document = JustHTML(html)
    return HtmlDocument(root=HtmlNode(document))


class HtmlNode:
    """Thin wrapper around a justhtml node (or document)."""

    def __init__(self, node):
        self._node = node

    @property
    def tag(self) -> str:
        return getattr(self._node, "tag", getattr(self._node, "name", "")) or ""

    @property
    def attrib(self) -> dict:
        attrs = getattr(self._node, "attrib", None)
        if attrs is None:
            attrs = getattr(self._node, "attrs", None)
        if attrs is None:
            attrs = getattr(self._node, "attributes", None)
        return dict(attrs) if attrs else {}

    @property
    def text(self) -> str:
        text = getattr(self._node, "text", None)
        if text is None and hasattr(self._node, "text_content"):
            text = self._node.text_content()
        return text or ""

    @property
    def tail(self) -> str:
        # justhtml does not expose tail text; compute from siblings in MOD-06
        return ""

    def parent(self) -> Optional["HtmlNode"]:
        parent = getattr(self._node, "parent", None)
        return HtmlNode(parent) if parent is not None else None

    def children(self) -> list["HtmlNode"]:
        kids = getattr(self._node, "children", None)
        if kids is None:
            kids = getattr(self._node, "child_nodes", None)
        if kids is None:
            return []
        return [HtmlNode(child) for child in kids]

    def iterchildren(self) -> Iterable["HtmlNode"]:
        return iter(self.children())

    def find(self, selector: str) -> Optional["HtmlNode"]:
        query = getattr(self._node, "query_selector", None)
        if query is None:
            return None
        found = query(selector)
        return HtmlNode(found) if found is not None else None

    def findall(self, selector: str) -> list["HtmlNode"]:
        query_all = getattr(self._node, "query_selector_all", None)
        if query_all is None:
            return []
        return [HtmlNode(node) for node in query_all(selector)]

    def getprevious(self) -> Optional["HtmlNode"]:
        siblings = self._sibling_nodes()
        for idx, node in enumerate(siblings):
            if node is self._node:
                if idx == 0:
                    return None
                return HtmlNode(siblings[idx - 1])
        return None

    def getnext(self) -> Optional["HtmlNode"]:
        siblings = self._sibling_nodes()
        for idx, node in enumerate(siblings):
            if node is self._node:
                if idx + 1 >= len(siblings):
                    return None
                return HtmlNode(siblings[idx + 1])
        return None

    def to_html(self) -> str:
        html = getattr(self._node, "html", None)
        if html is not None:
            return html
        outer = getattr(self._node, "outer_html", None)
        if outer is not None:
            return outer
        return str(self._node)

    def _sibling_nodes(self) -> list:
        parent = getattr(self._node, "parent", None)
        if parent is None:
            return []
        kids = getattr(parent, "children", None)
        if kids is None:
            kids = getattr(parent, "child_nodes", None)
        return list(kids) if kids is not None else []
