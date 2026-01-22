from __future__ import annotations

from dataclasses import replace

from .adapters.justhtml_adapter import parse_html
from .diagnostics import diagnostic_context, enforce_strict, extend_diagnostics
from .latex import infer_packages, serialize_document
from .models import ConvertOptions, LatexDocument
from .rewrite_pipeline import convert_document, normalize_document


class Converter:
    def __init__(self, options: ConvertOptions | None = None) -> None:
        self.options = options or ConvertOptions()
        self.diagnostics: tuple = ()

    def convert(self, html: str | bytes) -> LatexDocument:
        with diagnostic_context(enabled=True) as events:
            document, parse_events = parse_html(
                html,
                fragment=self.options.fragment,
                strict=False,
            )
            extend_diagnostics(parse_events)
            normalized = normalize_document(document, preserve_whitespace_tags={"pre"})
            latex_ast = convert_document(normalized)
            body = serialize_document(latex_ast)
            packages = tuple(sorted(infer_packages(latex_ast)))
            preamble = _build_preamble(packages, self.options.metadata)
            if self.options.strict:
                enforce_strict(events)
            result = LatexDocument(
                body=body,
                preamble=preamble,
                packages=packages,
                diagnostics=tuple(events),
            )
        self.diagnostics = result.diagnostics
        return result

    def with_options(self, **changes: object) -> "Converter":
        options = replace(self.options, **changes)
        return Converter(options=options)


def convert(html: str | bytes, *, options: ConvertOptions | None = None) -> LatexDocument:
    converter = Converter(options=options)
    return converter.convert(html)


def _build_preamble(packages: tuple[str, ...], metadata: dict[str, object]) -> str:
    lines = [f"\\usepackage{{{package}}}" for package in packages]
    extra = metadata.get("preamble")
    if extra:
        lines.append(str(extra))
    return "\n".join(lines)
