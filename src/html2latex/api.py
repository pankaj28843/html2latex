from __future__ import annotations

from dataclasses import replace

from .models import ConvertOptions, LatexDocument


class Converter:
    def __init__(self, options: ConvertOptions | None = None) -> None:
        self.options = options or ConvertOptions()
        self.diagnostics: tuple = ()

    def convert(self, html: str | bytes) -> LatexDocument:
        raise NotImplementedError("Rewrite pipeline not implemented yet")

    def with_options(self, **changes: object) -> "Converter":
        options = replace(self.options, **changes)
        return Converter(options=options)


def convert(html: str | bytes, *, options: ConvertOptions | None = None) -> LatexDocument:
    converter = Converter(options=options)
    return converter.convert(html)
