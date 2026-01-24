"""LaTeX Abstract Syntax Tree node types."""

from __future__ import annotations

from dataclasses import field

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

__all__ = [
    "LatexCommand",
    "LatexDocumentAst",
    "LatexEnvironment",
    "LatexGroup",
    "LatexNode",
    "LatexRaw",
    "LatexText",
]


@dataclass(config=ConfigDict(frozen=True))
class LatexText:
    """A text node containing escaped LaTeX content."""

    text: str


@dataclass(config=ConfigDict(frozen=True))
class LatexRaw:
    """A raw LaTeX node containing unescaped LaTeX code."""

    value: str


@dataclass(config=ConfigDict(frozen=True))
class LatexGroup:
    """A group of LaTeX nodes enclosed in braces."""

    children: tuple[LatexNode, ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class LatexCommand:
    """A LaTeX command with optional arguments and options."""

    name: str
    args: tuple[LatexGroup, ...] = ()
    options: tuple[str, ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class LatexEnvironment:
    """A LaTeX environment with begin/end tags."""

    name: str
    children: tuple[LatexNode, ...] = ()
    args: tuple[LatexGroup, ...] = ()
    options: tuple[str, ...] = ()


@dataclass(config=ConfigDict(frozen=True))
class LatexDocumentAst:
    """The root document AST containing preamble and body."""

    preamble: tuple[LatexNode, ...] = ()
    body: tuple[LatexNode, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


LatexNode = LatexText | LatexRaw | LatexGroup | LatexCommand | LatexEnvironment
