"""LaTeX AST serialization to string output."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from .ast import (
    LatexCommand,
    LatexDocumentAst,
    LatexEnvironment,
    LatexGroup,
    LatexNode,
    LatexRaw,
    LatexText,
)

if TYPE_CHECKING:
    from collections.abc import Iterable


class LatexSerializer(Protocol):
    """Protocol for LaTeX document serializers."""

    def serialize(self, document: LatexDocumentAst) -> str:  # pragma: no cover - interface only
        """Serialize a LaTeX document AST to string."""
        ...


def serialize_document(document: LatexDocumentAst, *, formatted: bool = False) -> str:
    """Serialize a LaTeX document AST to string.

    Args:
        document: The LaTeX document AST to serialize.
        formatted: If True, produce human-readable output with indentation.

    Returns:
        The serialized LaTeX string.
    """
    if formatted:
        serializer = IndentedSerializer()
        return serializer.serialize(document)
    return "".join(_serialize_node(node) for node in document.body)


# Environments that get indented content on new lines
_BLOCK_ENVIRONMENTS = frozenset(
    {
        "itemize",
        "enumerate",
        "description",
        "quote",
        "quotation",
        "center",
        "flushleft",
        "flushright",
        "figure",
        "table",
        "tabular",
        "tabularx",
    }
)

# Commands that need a newline after them (block-level)
_NEWLINE_AFTER_COMMANDS = frozenset(
    {
        "section",
        "subsection",
        "subsubsection",
        "paragraph",
        "subparagraph",
        "par",
        "item",
        "hrule",
        "newline",
        "setcounter",
        "addtocounter",
        "renewcommand",
    }
)


class IndentedSerializer:
    """Serializer that produces human-readable LaTeX with 2-space indentation."""

    def __init__(self) -> None:
        self._indent_level = 0
        self._indent_str = "  "  # 2 spaces

    def serialize(self, document: LatexDocumentAst) -> str:
        """Serialize document to formatted LaTeX string."""
        return self._serialize_nodes(document.body).rstrip()

    def _indent(self) -> str:
        return self._indent_str * self._indent_level

    def _serialize_nodes(self, nodes: list[LatexNode]) -> str:
        result: list[str] = []
        i = 0
        while i < len(nodes):
            node = nodes[i]
            text = self._serialize_node(node, nodes, i)
            result.append(text)
            i += 1
        return "".join(result)

    def _serialize_node(self, node: LatexNode, siblings: list[LatexNode], index: int) -> str:
        if isinstance(node, LatexText):
            return _escape_text(node.text)
        if isinstance(node, LatexRaw):
            return node.value
        if isinstance(node, LatexCommand):
            return self._serialize_command(node, siblings, index)
        if isinstance(node, LatexEnvironment):
            return self._serialize_environment(node, siblings, index)
        if isinstance(node, LatexGroup):  # pragma: no cover - groups are inside commands
            return self._serialize_group(node)
        return ""  # pragma: no cover - unreachable for valid AST

    def _serialize_command(self, cmd: LatexCommand, siblings: list[LatexNode], index: int) -> str:
        options = _format_options(cmd.options)
        args = "".join(self._serialize_group(group) for group in cmd.args)
        needs_newline = cmd.name in _NEWLINE_AFTER_COMMANDS

        if args:
            base = f"\\{cmd.name}{options}{args}"
        # Only add trailing space for commands without args when not followed by newline
        elif needs_newline:
            base = f"\\{cmd.name}{options}"
        else:
            base = f"\\{cmd.name}{options} "

        if needs_newline:
            return base + "\n"
        return base

    def _serialize_environment(
        self, env: LatexEnvironment, siblings: list[LatexNode], index: int
    ) -> str:
        options = _format_options(env.options)
        args = "".join(self._serialize_group(group) for group in env.args)

        if env.name in _BLOCK_ENVIRONMENTS:
            return self._serialize_block_environment(env, options, args, siblings, index)
        # Inline environment
        body = "".join(
            self._serialize_node(child, env.children, i) for i, child in enumerate(env.children)
        )
        return f"\\begin{{{env.name}}}{options}{args}{body}\\end{{{env.name}}}"

    def _serialize_block_environment(
        self,
        env: LatexEnvironment,
        options: str,
        args: str,
        siblings: list[LatexNode],
        index: int,
    ) -> str:
        lines: list[str] = []
        lines.append(f"{self._indent()}\\begin{{{env.name}}}{options}{args}")

        self._indent_level += 1
        body_lines = self._serialize_block_body(env)
        lines.extend(body_lines)
        self._indent_level -= 1

        lines.append(f"{self._indent()}\\end{{{env.name}}}")
        return "\n".join(lines)

    def _serialize_block_body(self, env: LatexEnvironment) -> list[str]:
        """Serialize body of a block environment with proper indentation."""
        lines: list[str] = []
        children = env.children
        consumed: set[int] = set()  # Track indices consumed by item processing

        i = 0
        while i < len(children):
            if i in consumed:
                i += 1
                continue
            child = children[i]
            if isinstance(child, LatexCommand) and child.name == "item":
                item_lines, new_consumed = self._serialize_item(child, children, i)
                consumed.update(new_consumed)
                lines.extend(item_lines)
            elif isinstance(child, LatexCommand) and child.name in _NEWLINE_AFTER_COMMANDS:
                # Commands like \setcounter, \renewcommand, etc.
                line = self._serialize_command_without_newline(child)
                lines.append(f"{self._indent()}{line}")
            elif isinstance(child, LatexEnvironment):
                env_text = self._serialize_environment(child, children, i)
                lines.append(env_text)
            elif isinstance(child, (LatexText, LatexRaw)):
                # Text nodes in block environments (like table rows)
                text = self._serialize_node(child, children, i).strip()
                if text:
                    lines.append(f"{self._indent()}{text}")
            else:
                text = self._serialize_node(child, children, i)
                if text.strip():
                    lines.append(f"{self._indent()}{text}")
            i += 1
        return lines

    def _serialize_item(
        self, item: LatexCommand, siblings: list[LatexNode], index: int
    ) -> tuple[list[str], set[int]]:
        r"""Serialize an \item command with its content. Returns (lines, consumed_indices)."""
        lines: list[str] = []
        consumed: set[int] = set()
        options = _format_options(item.options)

        # Collect content following this \item until next structural element
        content_parts: list[str] = []
        nested_envs: list[tuple[int, LatexEnvironment]] = []
        j = index + 1
        while j < len(siblings):
            next_node = siblings[j]
            if isinstance(next_node, LatexCommand) and next_node.name in {
                "item",
                "setcounter",
                "addtocounter",
                "renewcommand",
            }:
                break
            consumed.add(j)
            if isinstance(next_node, LatexEnvironment) and next_node.name in _BLOCK_ENVIRONMENTS:
                nested_envs.append((j, next_node))
                j += 1
                continue
            text = self._serialize_node(next_node, siblings, j)
            content_parts.append(text)
            j += 1

        content = "".join(content_parts).strip()

        # Build item line (args always empty, term goes in options)
        item_line = f"{self._indent()}\\item{options}"

        if content:
            item_line += f" {content}"
        lines.append(item_line)

        # Handle nested environments
        for _, nested_env in nested_envs:
            self._indent_level += 1
            env_text = self._serialize_environment(nested_env, siblings, index)
            lines.append(env_text)
            self._indent_level -= 1

        # Add blank line if next sibling is another \item
        if j < len(siblings):
            next_after = siblings[j]
            if isinstance(next_after, LatexCommand) and next_after.name == "item":
                lines.append("")

        return lines, consumed

    def _serialize_command_without_newline(self, cmd: LatexCommand) -> str:
        """Serialize a command without context-aware newlines (for block body commands)."""
        options = _format_options(cmd.options)
        args = "".join(self._serialize_group(group) for group in cmd.args)
        return f"\\{cmd.name}{options}{args}"

    def _serialize_group(self, group: LatexGroup) -> str:
        content = "".join(
            self._serialize_node(node, group.children, i) for i, node in enumerate(group.children)
        )
        return f"{{{content}}}"


def serialize_nodes(nodes: Iterable[LatexNode]) -> Iterable[str]:
    """Serialize a sequence of LaTeX nodes to strings.

    Args:
        nodes: The LaTeX nodes to serialize.

    Yields:
        Serialized string for each node.
    """
    for node in nodes:
        yield _serialize_node(node)


def infer_packages(document: LatexDocumentAst) -> set[str]:
    """Infer required LaTeX packages from document content.

    Args:
        document: The LaTeX document AST to analyze.

    Returns:
        Set of package names required by the document.
    """
    packages: set[str] = set()
    for node in _walk_nodes(document.body):
        if isinstance(node, LatexCommand) and node.name in {"href", "url"}:
            packages.add("hyperref")
        if isinstance(node, LatexCommand) and node.name == "includegraphics":
            packages.add("graphicx")
        if isinstance(node, LatexCommand) and node.name == "sout":
            packages.add("ulem")
        if isinstance(node, LatexCommand) and node.name in {"colorbox", "textcolor"}:
            packages.add("xcolor")
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
