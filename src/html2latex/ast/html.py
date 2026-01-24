"""HTML Abstract Syntax Tree node types."""

from __future__ import annotations

from dataclasses import field

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

__all__ = [
    "HtmlDocument",
    "HtmlElement",
    "HtmlNode",
    "HtmlText",
]


@dataclass(config=ConfigDict(frozen=True))
class HtmlText:
    """A text node in the HTML AST."""

    text: str


@dataclass(config=ConfigDict(frozen=True))
class HtmlElement:
    """An element node in the HTML AST."""

    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: tuple[HtmlNode, ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class HtmlDocument:
    """The root document node of the HTML AST."""

    children: tuple[HtmlNode, ...]
    doctype: str | None = None


HtmlNode = HtmlElement | HtmlText
