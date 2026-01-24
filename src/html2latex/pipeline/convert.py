"""HTML to LaTeX AST conversion pipeline."""

from __future__ import annotations

import re

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
from html2latex.tags import BLOCK_PASSTHROUGH, INLINE_PASSTHROUGH

__all__ = ["convert_document"]

_HEADING_COMMANDS = {
    "h1": "section",
    "h2": "subsection",
    "h3": "subsubsection",
    "h4": "paragraph",
    "h5": "subparagraph",
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
    "del": "sout",
    "s": "sout",
    "strike": "sout",
    # Semantic elements with LaTeX equivalents
    "ins": "underline",  # Inserted text
    "kbd": "texttt",  # Keyboard input
    "samp": "texttt",  # Sample output
    "var": "textit",  # Variable
    "cite": "textit",  # Citation/title
}


def convert_document(
    document: HtmlDocument,
) -> LatexDocumentAst:
    """Convert an HTML document AST to a LaTeX document AST.

    Args:
        document: The HTML document to convert.

    Returns:
        A LatexDocumentAst containing the converted content.
    """
    body = _convert_nodes(document.children)
    return LatexDocumentAst(body=body)


def _convert_nodes(
    nodes: tuple[HtmlNode, ...],
    list_level: int = 0,
    quote_level: int = 0,
) -> tuple[LatexNode, ...]:
    output: list[LatexNode] = []
    for node in nodes:
        output.extend(_convert_node(node, list_level, quote_level))
    return tuple(output)


def _convert_node(node: HtmlNode, list_level: int = 0, quote_level: int = 0) -> list[LatexNode]:
    if isinstance(node, HtmlText):
        return [LatexText(text=node.text)]

    if isinstance(node, HtmlElement):
        tag = node.tag.lower()
        if _is_math_container(node):
            return _convert_math(node)
        if tag in _INLINE_COMMANDS:
            children = _convert_nodes(node.children, list_level, quote_level)
            group = LatexGroup(children=children)
            return [LatexCommand(name=_INLINE_COMMANDS[tag], args=(group,))]

        if tag == "small":
            # Font size switch: {\small ...}
            children = _convert_nodes(node.children, list_level, quote_level)
            return [LatexRaw(value=r"{\small "), *children, LatexRaw(value="}")]

        if tag == "big":
            # Font size switch: {\large ...} (deprecated HTML tag)
            children = _convert_nodes(node.children, list_level, quote_level)
            return [LatexRaw(value=r"{\large "), *children, LatexRaw(value="}")]

        if tag == "mark":
            # Highlighted text → colorbox (requires xcolor package)
            children = _convert_nodes(node.children, list_level, quote_level)
            group = LatexGroup(children=children)
            color_group = LatexGroup(children=(LatexText(text="yellow"),))
            return [LatexCommand(name="colorbox", args=(color_group, group))]

        if tag in INLINE_PASSTHROUGH:
            return list(_convert_nodes(node.children, list_level, quote_level))

        if tag in _HEADING_COMMANDS:
            children = _convert_nodes(node.children, list_level, quote_level)
            group = LatexGroup(children=children)
            return [LatexCommand(name=_HEADING_COMMANDS[tag], args=(group,))]

        if tag == "br":
            return [LatexCommand(name="newline")]

        if tag == "center":
            # Deprecated <center> tag → center environment
            children = _convert_nodes(node.children, list_level, quote_level)
            return [LatexEnvironment(name="center", children=tuple(children))]

        if tag == "q":
            # Inline quote element - use LaTeX backtick/apostrophe quotes
            # Outer quotes: ``...''  Nested quotes: `...'
            children = _convert_nodes(node.children, list_level, quote_level + 1)
            if quote_level == 0:
                # Outer quote: double backticks and double apostrophes
                return [LatexRaw(value="``"), *children, LatexRaw(value="''")]
            # Nested quote: single backtick and single apostrophe
            return [LatexRaw(value="`"), *children, LatexRaw(value="'")]

        if tag in {"p", "div"}:
            # Check for text-align style
            style = node.attrs.get("style", "")
            align = _parse_text_align(style)
            children = _convert_nodes(node.children, list_level, quote_level)
            if align == "center":
                return [LatexEnvironment(name="center", children=tuple(children))]
            if align == "left":
                return [LatexEnvironment(name="flushleft", children=tuple(children))]
            if align == "right":
                return [LatexEnvironment(name="flushright", children=tuple(children))]
            return [*children, LatexCommand(name="par")]

        if tag == "hr":
            return [LatexCommand(name="hrule")]

        if tag == "a":
            href = node.attrs.get("href")
            children = _convert_nodes(node.children, list_level, quote_level)
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
            # Build options for width/height attributes
            options: list[str] = []
            width = node.attrs.get("width")
            height = node.attrs.get("height")
            if width:
                options.append(f"width={width}px")
            if height:
                options.append(f"height={height}px")
            return [
                LatexCommand(
                    name="includegraphics",
                    options=tuple(options),
                    args=(LatexGroup(children=(LatexText(text=src),)),),
                )
            ]

        if tag == "blockquote":
            children = _convert_nodes(node.children, list_level, quote_level)
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
            return _convert_table(node, list_level)

        if tag in {"ul", "ol"}:
            ordered = tag == "ol"
            reversed_list = False
            env = "itemize" if tag == "ul" else "enumerate"
            current_level = list_level + 1
            items: list[LatexNode] = []
            if ordered:
                reversed_list = "reversed" in node.attrs
                list_type = _parse_list_type(node.attrs.get("type"))
                if list_type is not None:
                    label_name = _list_label_name(current_level)
                    counter_name = _list_counter_name(current_level)
                    label_spec = LatexCommand(
                        name=list_type,
                        args=(LatexGroup(children=(LatexText(text=counter_name),)),),
                    )
                    items.append(
                        LatexCommand(
                            name="renewcommand",
                            args=(
                                LatexGroup(
                                    children=(LatexRaw(value=f"\\{label_name}"),),
                                ),
                                LatexGroup(
                                    children=(label_spec, LatexText(text=".")),
                                ),
                            ),
                        )
                    )
                raw_start = node.attrs.get("start")
                start = _parse_list_start(raw_start) if raw_start is not None else 1
                if reversed_list:
                    if raw_start is None:
                        start = _count_list_items(node)
                    if start >= 1:
                        counter_name = _list_counter_name(current_level)
                        items.append(
                            LatexCommand(
                                name="setcounter",
                                args=(
                                    LatexGroup(children=(LatexText(text=counter_name),)),
                                    LatexGroup(children=(LatexText(text=str(start + 1)),)),
                                ),
                            )
                        )
                elif start > 1:
                    counter_name = _list_counter_name(current_level)
                    items.append(
                        LatexCommand(
                            name="setcounter",
                            args=(
                                LatexGroup(children=(LatexText(text=counter_name),)),
                                LatexGroup(children=(LatexText(text=str(start - 1)),)),
                            ),
                        )
                    )
            for child in node.children:
                if isinstance(child, HtmlElement) and child.tag.lower() == "li":
                    items.extend(_convert_list_item(child, current_level, ordered, reversed_list))
            return [LatexEnvironment(name=env, children=tuple(items))]

        if tag == "dl":
            items = _convert_description_list(node.children, list_level)
            return [LatexEnvironment(name="description", children=tuple(items))]

        if tag == "figure":
            return _convert_figure(node, list_level)

        if tag == "figcaption":
            # figcaption outside figure - just render content
            children = _convert_nodes(node.children, list_level, quote_level)
            return list(children)

        if tag in BLOCK_PASSTHROUGH:
            children = _convert_nodes(node.children, list_level, quote_level)
            return list(children)

        children = _convert_nodes(node.children, list_level, quote_level)
        return list(children)

    return []


def _convert_list_item(
    node: HtmlElement,
    list_level: int,
    ordered: bool,
    reversed_list: bool,
) -> list[LatexNode]:
    prefix: list[LatexNode] = []
    if ordered and reversed_list:
        counter_name = _list_counter_name(list_level)
        prefix.append(
            LatexCommand(
                name="addtocounter",
                args=(
                    LatexGroup(children=(LatexText(text=counter_name),)),
                    LatexGroup(children=(LatexText(text="-2"),)),
                ),
            )
        )
    if ordered and not reversed_list:
        value = _parse_list_value(node.attrs.get("value"))
        if value is not None and value != 1:
            counter_name = _list_counter_name(list_level)
            prefix.append(
                LatexCommand(
                    name="setcounter",
                    args=(
                        LatexGroup(children=(LatexText(text=counter_name),)),
                        LatexGroup(children=(LatexText(text=str(value - 1)),)),
                    ),
                )
            )
    children = _convert_nodes(node.children, list_level)
    return [*prefix, LatexCommand(name="item"), *children]


def _convert_description_list(
    children: tuple[HtmlNode, ...],
    list_level: int,
) -> list[LatexNode]:
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
            items.extend(_convert_nodes(child.children, list_level))
            pending_label = None

    if pending_label:
        items.append(LatexCommand(name="item", options=(pending_label,)))
    return items


def _parse_list_start(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        return 1
    return max(1, parsed)


def _parse_list_value(value: str | None) -> int | None:
    if value is None:
        return None
    try:
        parsed = int(value)
    except ValueError:
        return None
    return parsed if parsed >= 1 else None


def _parse_list_type(value: str | None) -> str | None:
    if value is None:
        return None
    mapping = {
        "1": "arabic",
        "a": "alph",
        "A": "Alph",
        "i": "roman",
        "I": "Roman",
    }
    return mapping.get(value)


_TEXT_ALIGN_RE = re.compile(r"text-align\s*:\s*(left|center|right)", re.IGNORECASE)


def _parse_text_align(style: str) -> str | None:
    """Extract text-align value from CSS style string."""
    match = _TEXT_ALIGN_RE.search(style)
    if match:
        return match.group(1).lower()
    return None


def _parse_cell_align(node: HtmlElement) -> str:
    """Extract alignment for a table cell (td/th).

    Checks both the legacy 'align' attribute and CSS 'style' attribute.
    Returns LaTeX column spec character: 'l', 'c', or 'r'.
    Defaults to 'l' (left) if no alignment specified.
    """
    # Check legacy align attribute first
    align_attr = node.attrs.get("align", "").lower()
    if align_attr in ("left", "center", "right"):
        return {"left": "l", "center": "c", "right": "r"}[align_attr]

    # Check CSS style attribute
    style = node.attrs.get("style", "")
    text_align = _parse_text_align(style)
    if text_align in ("left", "center", "right"):
        return {"left": "l", "center": "c", "right": "r"}[text_align]

    return "l"  # Default to left


def _detect_column_alignments(
    all_row_cells: list[list[HtmlElement]],
    max_columns: int,
) -> list[str]:
    """Detect dominant alignment for each column.

    Analyzes all cells in each column and returns the most common alignment.
    Cells with colspan > 1 are excluded from the count since they use multicolumn.
    """
    # Count alignments per column
    column_counts: list[dict[str, int]] = [{"l": 0, "c": 0, "r": 0} for _ in range(max_columns)]

    for row_cells in all_row_cells:
        col = 0
        for cell in row_cells:
            if col >= max_columns:
                break
            colspan = _parse_span(cell.attrs.get("colspan"))
            # Only count single-cell alignments (colspan cells use multicolumn)
            if colspan == 1:
                align = _parse_cell_align(cell)
                column_counts[col][align] += 1
            col += colspan

    # Determine dominant alignment for each column
    alignments: list[str] = []
    for counts in column_counts:
        # Find the most common alignment (prefer 'l' on ties)
        max_count = max(counts.values())
        if counts["l"] == max_count:
            alignments.append("l")
        elif counts["c"] == max_count:
            alignments.append("c")
        else:
            alignments.append("r")

    return alignments


def _count_list_items(node: HtmlElement) -> int:
    return sum(
        1 for child in node.children if isinstance(child, HtmlElement) and child.tag.lower() == "li"
    )


def _list_counter_name(level: int) -> str:
    counters = ("enumi", "enumii", "enumiii", "enumiv")
    index = min(max(level, 1), len(counters)) - 1
    return counters[index]


def _list_label_name(level: int) -> str:
    return f"label{_list_counter_name(level)}"


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


def _convert_figure(figure: HtmlElement, list_level: int) -> list[LatexNode]:
    """Convert HTML <figure> to LaTeX figure environment."""
    content: list[LatexNode] = []
    caption: LatexCommand | None = None

    for child in figure.children:
        if not isinstance(child, HtmlElement):
            continue
        tag = child.tag.lower()
        if tag == "figcaption":
            nodes = _convert_nodes(child.children, list_level)
            # Remove \par from caption content
            filtered: list[LatexNode] = []
            for node in nodes:
                if isinstance(node, LatexCommand) and node.name == "par":
                    if filtered:
                        filtered.append(LatexText(text=" "))
                else:
                    filtered.append(node)
            while filtered and isinstance(filtered[-1], LatexText) and filtered[-1].text == " ":
                filtered.pop()
            if filtered:
                caption = LatexCommand(name="caption", args=(LatexGroup(children=tuple(filtered)),))
        else:
            content.extend(_convert_node(child, list_level))

    if not content and caption is None:
        return []

    # Add centering and caption to figure environment
    figure_content: list[LatexNode] = [LatexCommand(name="centering")]
    figure_content.extend(content)
    if caption:
        figure_content.append(caption)

    return [LatexEnvironment(name="figure", children=tuple(figure_content))]


def _convert_table(table: HtmlElement, list_level: int) -> list[LatexNode]:
    rows = _collect_table_rows(table)
    if not rows:
        return []

    row_cells = [_extract_row_cells(row) for row in rows]

    # Calculate max columns accounting for colspan
    max_columns = max((_row_colspan(cells) for cells in row_cells), default=0)
    if max_columns <= 0:
        return []

    # Detect column alignments from cell attributes
    column_alignments = _detect_column_alignments(row_cells, max_columns)

    # Render rows with rowspan tracking and alignment
    rendered_rows = _render_table_rows(row_cells, max_columns, list_level)

    column_spec = LatexGroup(children=(LatexText(text="".join(column_alignments)),))
    tabular = LatexEnvironment(
        name="tabular",
        args=(column_spec,),
        children=tuple(LatexRaw(value=row) for row in rendered_rows),
    )

    caption = _extract_table_caption(table, list_level)
    if caption is None:
        return [tabular]
    return [
        LatexEnvironment(
            name="table",
            children=(caption, tabular),
        )
    ]


def _render_table_rows(
    all_row_cells: list[list[HtmlElement]],
    max_columns: int,
    list_level: int,
) -> list[str]:
    """Render table rows with rowspan support using multirow.

    Tracks which columns are "occupied" by cells spanning multiple rows
    and inserts empty placeholders in subsequent rows.
    """
    # occupied[col] = number of rows remaining that this column is occupied
    occupied: dict[int, int] = {}
    rendered_rows: list[str] = []

    for row_cells in all_row_cells:
        rendered_cells: list[str] = []
        col = 0
        cell_idx = 0

        while col < max_columns:
            # Check if this column is occupied by a rowspan from a previous row
            if col in occupied and occupied[col] > 0:
                rendered_cells.append("")  # Empty placeholder for multirow
                occupied[col] -= 1
                if occupied[col] == 0:
                    del occupied[col]
                col += 1
                continue

            # Get the next cell from this row
            if cell_idx < len(row_cells):
                cell = row_cells[cell_idx]
                cell_idx += 1

                colspan = _parse_span(cell.attrs.get("colspan"))
                rowspan = _parse_span(cell.attrs.get("rowspan"))

                content = _render_cell_content(cell, list_level)

                # Get the cell's alignment
                cell_align = _parse_cell_align(cell)

                # Handle rowspan with multirow
                if rowspan > 1:
                    # Mark columns as occupied for subsequent rows
                    for c in range(col, col + colspan):
                        occupied[c] = rowspan - 1
                    # Wrap content in multirow
                    if colspan > 1:
                        # multirow inside multicolumn - use cell's alignment
                        content = f"\\multicolumn{{{colspan}}}{{{cell_align}}}{{\\multirow{{{rowspan}}}{{*}}{{{content}}}}}"
                    else:
                        content = f"\\multirow{{{rowspan}}}{{*}}{{{content}}}"
                elif colspan > 1:
                    # Use cell's alignment for multicolumn
                    content = f"\\multicolumn{{{colspan}}}{{{cell_align}}}{{{content}}}"

                rendered_cells.append(content)
                col += colspan
            else:
                # No more cells in this row - fill with empty
                rendered_cells.append("")
                col += 1

        row = " & ".join(rendered_cells).rstrip()
        rendered_rows.append(f"{row} \\\\")

    return rendered_rows


def _render_cell_content(cell: HtmlElement, list_level: int) -> str:
    """Render cell content, applying bold for th elements."""
    children = _convert_nodes(cell.children, list_level)
    tag = cell.tag.lower()
    if tag == "th":
        group = LatexGroup(children=tuple(children))
        children = [LatexCommand(name="textbf", args=(group,))]
    return "".join(serialize_nodes(children))


def _collect_table_rows(table: HtmlElement) -> list[HtmlElement]:
    rows: list[HtmlElement] = []
    for child in table.children:
        if not isinstance(child, HtmlElement):
            continue
        tag = child.tag.lower()
        if tag in {"thead", "tbody", "tfoot"}:
            rows.extend(
                grandchild
                for grandchild in child.children
                if isinstance(grandchild, HtmlElement) and grandchild.tag.lower() == "tr"
            )
        elif tag == "tr":
            rows.append(child)
    return rows


def _extract_table_caption(
    table: HtmlElement,
    list_level: int,
) -> LatexCommand | None:
    for child in table.children:
        if not isinstance(child, HtmlElement):
            continue
        if child.tag.lower() != "caption":
            continue
        nodes = _convert_nodes(child.children, list_level)
        # Replace \par with separating space to avoid word concatenation when
        # caption contains multiple block children (e.g., multiple <p> tags)
        new_nodes: list[LatexNode] = []
        for node in nodes:
            if isinstance(node, LatexCommand) and node.name == "par":
                if new_nodes:
                    new_nodes.append(LatexText(text=" "))
            else:
                new_nodes.append(node)
        # Strip any trailing space added from final \par
        while new_nodes and isinstance(new_nodes[-1], LatexText) and new_nodes[-1].text == " ":
            new_nodes.pop()
        nodes = tuple(new_nodes)
        if not nodes:
            return None
        group = LatexGroup(children=nodes)
        return LatexCommand(name="caption", args=(group,))
    return None


def _extract_row_cells(row: HtmlElement) -> list[HtmlElement]:
    return [
        child
        for child in row.children
        if isinstance(child, HtmlElement) and child.tag.lower() in {"td", "th"}
    ]


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
