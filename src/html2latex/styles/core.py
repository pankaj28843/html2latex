from __future__ import annotations

from dataclasses import field
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

TextAlign = Literal["left", "right", "center", "justify"]


@dataclass(config=ConfigDict(frozen=True))
class ParagraphStyle:
    align: TextAlign = "justify"
    space_before: float = 0.0
    space_after: float = 0.0


@dataclass(config=ConfigDict(frozen=True))
class ListStyle:
    kind: Literal["itemize", "enumerate", "description"] = "itemize"
    label: str | None = None


@dataclass(config=ConfigDict(frozen=True))
class TableStyle:
    align: TextAlign = "left"
    header_bold: bool = True
    borders: bool = False


@dataclass(config=ConfigDict(frozen=True))
class ImageStyle:
    max_width: str | None = None
    max_height: str | None = None
    placement: str = "htbp"


@dataclass(config=ConfigDict(frozen=True))
class HeadingStyle:
    levels: tuple[str, ...] = ("section", "subsection", "subsubsection")


@dataclass(config=ConfigDict(frozen=True))
class StyleConfig:
    paragraph: ParagraphStyle = field(default_factory=ParagraphStyle)
    list: ListStyle = field(default_factory=ListStyle)
    table: TableStyle = field(default_factory=TableStyle)
    image: ImageStyle = field(default_factory=ImageStyle)
    heading: HeadingStyle = field(default_factory=HeadingStyle)
