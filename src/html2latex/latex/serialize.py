from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

from .ast import (
    LatexCommand,
    LatexDocumentAst,
    LatexEnvironment,
    LatexGroup,
    LatexNode,
    LatexRaw,
    LatexText,
)


class LatexSerializer(Protocol):
    def serialize(self, document: LatexDocumentAst) -> str:  # pragma: no cover - interface only
        ...


def serialize_document(document: LatexDocumentAst) -> str:
    return "".join(_serialize_node(node) for node in document.body)


def serialize_nodes(nodes: Iterable[LatexNode]) -> Iterable[str]:
    for node in nodes:
        yield _serialize_node(node)


def infer_packages(document: LatexDocumentAst) -> set[str]:
    packages: set[str] = set()
    for node in _walk_nodes(document.body):
        if isinstance(node, LatexCommand) and node.name in {"href", "url"}:
            packages.add("hyperref")
        if isinstance(node, LatexCommand) and node.name == "includegraphics":
            packages.add("graphicx")
        if isinstance(node, LatexCommand) and node.name == "sout":
            packages.add("ulem")
        if isinstance(node, LatexEnvironment) and node.name == "tabularx":
            packages.add("tabularx")
    return packages


def _walk_nodes(nodes: Iterable[LatexNode]) -> Iterable[LatexNode]:
    for node in nodes:
        yield node
        if isinstance(node, LatexCommand):
            for group in node.args:
                yield from _walk_nodes(group.children)
        if isinstance(node, LatexEnvironment):
            yield from _walk_nodes(node.children)
            for group in node.args:
                yield from _walk_nodes(group.children)
        if isinstance(node, LatexGroup):
            yield from _walk_nodes(node.children)


def _serialize_node(node: LatexNode) -> str:
    if isinstance(node, LatexText):
        return _escape_text(node.text)
    if isinstance(node, LatexRaw):
        return node.value
    if isinstance(node, LatexCommand):
        return _serialize_command(node)
    if isinstance(node, LatexEnvironment):
        return _serialize_environment(node)
    if isinstance(node, LatexGroup):
        return _serialize_group(node)
    return ""


def _serialize_command(command: LatexCommand) -> str:
    options = _format_options(command.options)
    args = "".join(_serialize_group(group) for group in command.args)
    if args:
        return f"\\{command.name}{options}{args}"
    return f"\\{command.name}{options} "


def _serialize_environment(env: LatexEnvironment) -> str:
    options = _format_options(env.options)
    args = "".join(_serialize_group(group) for group in env.args)
    body = "".join(_serialize_node(child) for child in env.children)
    return f"\\begin{{{env.name}}}{options}{args}{body}\\end{{{env.name}}}"


def _serialize_group(group: LatexGroup) -> str:
    content = "".join(_serialize_node(node) for node in group.children)
    return f"{{{content}}}"


def _format_options(options: tuple[str, ...]) -> str:
    if not options:
        return ""
    return f"[{','.join(options)}]"


def _escape_text(text: str) -> str:
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(replacements.get(ch, ch) for ch in text)
