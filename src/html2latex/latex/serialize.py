from __future__ import annotations

from typing import Protocol

from .ast import LatexDocumentAst


class LatexSerializer(Protocol):
    def serialize(self, document: LatexDocumentAst) -> str:  # pragma: no cover - interface only
        ...
