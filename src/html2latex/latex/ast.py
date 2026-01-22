from __future__ import annotations

from dataclasses import field

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(frozen=True))
class LatexText:
    text: str


@dataclass(config=ConfigDict(frozen=True))
class LatexRaw:
    value: str


@dataclass(config=ConfigDict(frozen=True))
class LatexGroup:
    children: tuple["LatexNode", ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class LatexCommand:
    name: str
    args: tuple[LatexGroup, ...] = ()
    options: tuple[str, ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class LatexEnvironment:
    name: str
    children: tuple["LatexNode", ...] = ()
    args: tuple[LatexGroup, ...] = ()
    options: tuple[str, ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class LatexDocumentAst:
    preamble: tuple["LatexNode", ...] = ()
    body: tuple["LatexNode", ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


LatexNode = LatexText | LatexRaw | LatexGroup | LatexCommand | LatexEnvironment
