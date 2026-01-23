from __future__ import annotations

from dataclasses import field

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(frozen=True))
class HtmlText:
    text: str


@dataclass(config=ConfigDict(frozen=True))
class HtmlElement:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    children: tuple[HtmlNode, ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class HtmlDocument:
    children: tuple[HtmlNode, ...]
    doctype: str | None = None


HtmlNode = HtmlElement | HtmlText
