from __future__ import annotations

from html2latex.ast import HtmlDocument, HtmlElement, HtmlNode, HtmlText
from html2latex.latex import (
    LatexCommand,
    LatexDocumentAst,
    LatexEnvironment,
    LatexGroup,
    LatexNode,
    LatexRaw,
    LatexText,
    serialize_nodes,
)
from html2latex.styles import StyleConfig

_HEADING_COMMANDS = {
    "h1": "section",
    "h2": "subsection",
    "h3": "subsubsection",
}

_INLINE_COMMANDS = {
    "strong": "textbf",
    "b": "textbf",
    "em": "textit",
    "i": "textit",
    "u": "underline",
    "code": "texttt",
    "sup": "textsuperscript",
    "sub": "textsubscript",
}

_INLINE_PASSTHROUGH = {
    "abbr",
    "cite",
    "del",
    "dfn",
    "kbd",
    "mark",
    "s",
    "samp",
    "small",
    "span",
    "strike",
    "time",
    "var",
}

_BLOCK_PASSTHROUGH = {
    "article",
    "aside",
    "figure",
    "figcaption",
    "footer",
    "header",
    "main",
    "nav",
    "section",
}


def convert_document(
    document: HtmlDocument,
    *,
    style: StyleConfig | None = None,
) -> LatexDocumentAst:
    body = _convert_nodes(document.children)
    return LatexDocumentAst(body=body)


def _convert_nodes(nodes: tuple[HtmlNode, ...]) -> tuple[LatexNode, ...]:
    output: list[LatexNode] = []
    for node in nodes:
        output.extend(_convert_node(node))
    return tuple(output)


def _convert_node(node: HtmlNode) -> list[LatexNode]:
    if isinstance(node, HtmlText):
        return [LatexText(text=node.text)]

    if isinstance(node, HtmlElement):
        tag = node.tag.lower()
        if _is_math_container(node):
            return _convert_math(node)
        if tag in _INLINE_COMMANDS:
            children = _convert_nodes(node.children)
            group = LatexGroup(children=children)
            return [LatexCommand(name=_INLINE_COMMANDS[tag], args=(group,))]

        if tag in _INLINE_PASSTHROUGH:
            return list(_convert_nodes(node.children))

        if tag in _HEADING_COMMANDS:
            children = _convert_nodes(node.children)
            group = LatexGroup(children=children)
            return [LatexCommand(name=_HEADING_COMMANDS[tag], args=(group,))]

        if tag == "br":
            return [LatexCommand(name="newline")]

        if tag in {"p", "div"}:
            children = _convert_nodes(node.children)
            return [*children, LatexCommand(name="par")]

        if tag == "hr":
            return [LatexCommand(name="hrule")]

        if tag == "a":
            href = node.attrs.get("href")
            children = _convert_nodes(node.children)
            if not href:
                return list(children)
            href_group = LatexGroup(children=(LatexText(text=href),))
            if children:
                label_group = LatexGroup(children=tuple(children))
                return [
                    LatexCommand(
                        name="href",
                        args=(href_group, label_group),
                    )
                ]
            return [LatexCommand(name="url", args=(href_group,))]

        if tag == "img":
            src = node.attrs.get("src")
            alt = node.attrs.get("alt")
            if not src:
                return [LatexText(text=alt)] if alt else []
            return [
                LatexCommand(
                    name="includegraphics",
                    args=(LatexGroup(children=(LatexText(text=src),)),),
                )
            ]

        if tag == "blockquote":
            children = _convert_nodes(node.children)
            return [LatexEnvironment(name="quote", children=tuple(children))]

        if tag == "pre":
            content = _extract_text(node)
            return [
                LatexEnvironment(
                    name="verbatim",
                    children=(LatexRaw(value=content),),
                )
            ]

        if tag == "table":
            return _convert_table(node)

        if tag in {"ul", "ol"}:
            env = "itemize" if tag == "ul" else "enumerate"
            items: list[LatexNode] = []
            for child in node.children:
                if isinstance(child, HtmlElement) and child.tag.lower() == "li":
                    items.extend(_convert_list_item(child))
            return [LatexEnvironment(name=env, children=tuple(items))]

        if tag == "dl":
            items = _convert_description_list(node.children)
            return [LatexEnvironment(name="description", children=tuple(items))]

        if tag in _BLOCK_PASSTHROUGH:
            children = _convert_nodes(node.children)
            return list(children)

        children = _convert_nodes(node.children)
        return list(children)

    return []


def _convert_list_item(node: HtmlElement) -> list[LatexNode]:
    children = _convert_nodes(node.children)
    return [LatexCommand(name="item"), *children]


def _convert_description_list(children: tuple[HtmlNode, ...]) -> list[LatexNode]:
    items: list[LatexNode] = []
    pending_label: str | None = None

    for child in children:
        if not isinstance(child, HtmlElement):
            continue
        tag = child.tag.lower()
        if tag == "dt":
            pending_label = _extract_text(child).strip() or None
            continue
        if tag == "dd":
            options = (pending_label,) if pending_label else ()
            items.append(LatexCommand(name="item", options=options))
            items.extend(_convert_nodes(child.children))
            pending_label = None

    if pending_label:
        items.append(LatexCommand(name="item", options=(pending_label,)))
    return items


def _extract_text(node: HtmlElement) -> str:
    parts: list[str] = []
    for child in node.children:
        if isinstance(child, HtmlText):
            parts.append(child.text)
        elif isinstance(child, HtmlElement):
            parts.append(_extract_text(child))
    return "".join(parts)


def _is_math_container(node: HtmlElement) -> bool:
    if node.tag.lower() == "math":
        return True
    attrs = node.attrs
    if "data-latex" in attrs or "data-math" in attrs:
        return True
    classes = _class_set(attrs.get("class"))
    return bool(classes & {"math-tex", "math-tex-block", "math-display", "math-inline"})


def _convert_math(node: HtmlElement) -> list[LatexNode]:
    content = _extract_math_payload(node).strip()
    if not content:
        return []
    content, display_override = _strip_math_delimiters(content)
    display = display_override if display_override is not None else _is_display_math(node)
    if display:
        return [LatexRaw(value=f"\\[{content}\\]")]
    return [LatexRaw(value=f"\\({content}\\)")]


def _extract_math_payload(node: HtmlElement) -> str:
    if "data-latex" in node.attrs:
        return node.attrs["data-latex"]
    if "data-math" in node.attrs:
        return node.attrs["data-math"]
    return _extract_text(node)


def _strip_math_delimiters(text: str) -> tuple[str, bool | None]:
    if text.startswith("\\[") and text.endswith("\\]"):
        return text[2:-2].strip(), True
    if text.startswith("\\(") and text.endswith("\\)"):
        return text[2:-2].strip(), False
    if text.startswith("$$") and text.endswith("$$") and len(text) >= 4:
        return text[2:-2].strip(), True
    if text.startswith("$") and text.endswith("$") and len(text) >= 2:
        return text[1:-1].strip(), False
    return text, None


def _is_display_math(node: HtmlElement) -> bool:
    tag = node.tag.lower()
    if tag in {"div", "p"}:
        return True
    classes = _class_set(node.attrs.get("class"))
    return bool(classes & {"math-tex-block", "math-display"})


def _class_set(value: str | None) -> set[str]:
    if not value:
        return set()
    return {part for part in value.split() if part}


def _convert_table(table: HtmlElement) -> list[LatexNode]:
    rows = _collect_table_rows(table)
    if not rows:
        return []

    row_cells = [_extract_row_cells(row) for row in rows]
    max_columns = max((_row_colspan(cells) for cells in row_cells), default=0)
    if max_columns <= 0:
        return []

    column_spec = LatexGroup(children=(LatexText(text="l" * max_columns),))
    rendered_rows = [LatexRaw(value=_render_row(cells, max_columns)) for cells in row_cells]
    return [
        LatexEnvironment(
            name="tabular",
            args=(column_spec,),
            children=tuple(rendered_rows),
        )
    ]


def _collect_table_rows(table: HtmlElement) -> list[HtmlElement]:
    rows: list[HtmlElement] = []
    for child in table.children:
        if not isinstance(child, HtmlElement):
            continue
        tag = child.tag.lower()
        if tag in {"thead", "tbody", "tfoot"}:
            for grandchild in child.children:
                if isinstance(grandchild, HtmlElement) and grandchild.tag.lower() == "tr":
                    rows.append(grandchild)
        elif tag == "tr":
            rows.append(child)
    return rows


def _extract_row_cells(row: HtmlElement) -> list[HtmlElement]:
    cells: list[HtmlElement] = []
    for child in row.children:
        if isinstance(child, HtmlElement) and child.tag.lower() in {"td", "th"}:
            cells.append(child)
    return cells


def _row_colspan(cells: list[HtmlElement]) -> int:
    return sum(_parse_span(cell.attrs.get("colspan")) for cell in cells)


def _parse_span(value: str | None) -> int:
    if value is None:
        return 1
    try:
        parsed = int(value)
    except ValueError:
        return 1
    return parsed if parsed > 0 else 1


def _render_row(cells: list[HtmlElement], max_columns: int) -> str:
    rendered: list[str] = []
    used_columns = 0
    for cell in cells:
        span = _parse_span(cell.attrs.get("colspan"))
        rendered.append(_render_cell(cell, span))
        used_columns += span

    while used_columns < max_columns:
        rendered.append("")
        used_columns += 1

    row = " & ".join(rendered).rstrip()
    return f"{row} \\\\"


def _render_cell(cell: HtmlElement, span: int) -> str:
    children = _convert_nodes(cell.children)
    tag = cell.tag.lower()
    if tag == "th":
        group = LatexGroup(children=tuple(children))
        children = [LatexCommand(name="textbf", args=(group,))]
    content = "".join(serialize_nodes(children))
    if span > 1:
        return f"\\multicolumn{{{span}}}{{l}}{{{content}}}"
    return content
