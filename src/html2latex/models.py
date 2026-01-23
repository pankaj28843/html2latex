from __future__ import annotations

from dataclasses import field
from typing import Any

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(frozen=True))
class ConvertOptions:
    strict: bool = True
    fragment: bool = True
    formatted: bool = True
    template: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(config=ConfigDict(frozen=True))
class LatexDocument:
    body: str
    preamble: str = ""
    packages: tuple[str, ...] = ()
    diagnostics: tuple["Diagnostic", ...] = ()


Diagnostic = Any
