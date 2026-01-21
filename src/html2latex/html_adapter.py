"""justhtml adapter for a small lxml-like surface area."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from justhtml import JustHTML, ParseError
from justhtml.node import Comment, Element, Text


@dataclass
class HtmlDocument:
    root: "HtmlNode"
    errors: list[ParseError] | None = None


def parse_html(
    html: str,
    *,
    fragment: bool = True,
    collect_errors: bool = False,
    track_node_locations: bool = False,
) -> HtmlDocument:
    document = JustHTML(
        html,
        fragment=fragment,
        safe=False,
        collect_errors=collect_errors,
        track_node_locations=track_node_locations,
    )
    return HtmlDocument(
        root=HtmlNode(document.root),
        errors=document.errors if collect_errors else [],
    )


def is_comment(node: "HtmlNode") -> bool:
    return isinstance(node._node, Comment)


class HtmlNode:
    """Thin wrapper around a justhtml node (Element or DocumentFragment)."""

    def __init__(self, node):
        self._node = node

    @property
    def tag(self) -> str:
        if isinstance(self._node, Element):
            return self._node.name or ""
        return ""

    @tag.setter
    def tag(self, value: str) -> None:
        if isinstance(self._node, Element):
            self._node.name = value

    @property
    def attrib(self) -> dict:
        if isinstance(self._node, Element):
            return self._node.attrs
        return {}

    @property
    def text(self) -> str:
        if isinstance(self._node, Text):
            return self._node.data or ""
        if isinstance(self._node, Element):
            return _leading_text(self._node)
        return ""

    @property
    def tail(self) -> str:
        if isinstance(self._node, Element):
            return _tail_text(self._node)
        return ""

    def getparent(self) -> Optional["HtmlNode"]:
        parent = getattr(self._node, "parent", None)
        if parent is None:
            return None
        return HtmlNode(parent)

    def children(self) -> list["HtmlNode"]:
        return [HtmlNode(child) for child in _element_children(self._node)]

    def iterchildren(self) -> Iterable["HtmlNode"]:
        return iter(self.children())

    def iterdescendants(self) -> Iterable["HtmlNode"]:
        for child in _element_children(self._node):
            yield HtmlNode(child)
            for desc in HtmlNode(child).iterdescendants():
                yield desc

    def find(self, selector: str) -> Optional["HtmlNode"]:
        matches = self.findall(selector)
        return matches[0] if matches else None

    def findall(self, selector: str) -> list["HtmlNode"]:
        path = selector.strip()
        if path.startswith(".//"):
            path = path[3:]
        if path.startswith("//"):
            path = path[2:]
        parts = [p for p in path.split("/") if p]
        if not parts:
            return []
        if len(parts) == 1:
            return [HtmlNode(node) for node in _find_all(self._node, parts[0])]
        if len(parts) == 2:
            parent_tag, child_tag = parts
            return [
                HtmlNode(node)
                for node in _find_all(self._node, child_tag)
                if isinstance(node.parent, Element) and node.parent.name == parent_tag
            ]
        # Fallback: best-effort on last tag
        return [HtmlNode(node) for node in _find_all(self._node, parts[-1])]

    def getprevious(self) -> Optional["HtmlNode"]:
        siblings = _element_siblings(self._node)
        for idx, node in enumerate(siblings):
            if node is self._node:
                return HtmlNode(siblings[idx - 1]) if idx > 0 else None
        return None

    def getnext(self) -> Optional["HtmlNode"]:
        siblings = _element_siblings(self._node)
        for idx, node in enumerate(siblings):
            if node is self._node:
                return HtmlNode(siblings[idx + 1]) if idx + 1 < len(siblings) else None
        return None

    def to_html(self) -> str:
        if hasattr(self._node, "to_html"):
            return self._node.to_html(pretty=False)
        return str(self._node)

    def set(self, key: str, value: str) -> None:
        if isinstance(self._node, Element):
            self._node.attrs[key] = value

    def remove(self, child: "HtmlNode") -> None:
        if not isinstance(self._node, Element):
            return
        target = child._node if isinstance(child, HtmlNode) else child
        if hasattr(self._node, "remove_child"):
            self._node.remove_child(target)
        elif hasattr(self._node, "remove"):
            self._node.remove(target)

    def __iter__(self):
        return self.iterchildren()


def _element_children(node) -> list[Element]:
    children = getattr(node, "children", None)
    if not children:
        return []
    return [child for child in children if isinstance(child, Element)]


def _element_siblings(node) -> list[Element]:
    parent = getattr(node, "parent", None)
    if parent is None:
        return []
    return _element_children(parent)


def _leading_text(node: Element) -> str:
    parts = []
    for child in node.children:
        if isinstance(child, Text):
            parts.append(child.data or "")
        else:
            break
    return "".join(parts)


def _tail_text(node: Element) -> str:
    parent = getattr(node, "parent", None)
    if parent is None:
        return ""
    siblings = parent.children
    try:
        idx = siblings.index(node)
    except ValueError:
        return ""
    parts = []
    for sibling in siblings[idx + 1 :]:
        if isinstance(sibling, Text):
            parts.append(sibling.data or "")
        else:
            break
    return "".join(parts)


def _find_all(node, tag: str) -> list[Element]:
    matches = []
    for child in getattr(node, "children", []):
        if isinstance(child, Element):
            if child.name == tag:
                matches.append(child)
            matches.extend(_find_all(child, tag))
    return matches
