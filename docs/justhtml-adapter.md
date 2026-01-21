# justhtml Adapter Design (Spike)

Status: Spike-only (not integrated)

## Goals
- Replace lxml with justhtml without rewriting the core transformation logic all at once.
- Provide a narrow adapter interface that mimics the subset of lxml APIs used today.
- Keep parsing, traversal, and selection behind one boundary for testing and future swaps.

## Current lxml Usage (summary)
The codebase relies on these behaviors:
- Parse HTML: `etree.HTML(...)`, `document_fromstring(...)`.
- Node attributes: `tag`, `attrib`, `text`, `tail`.
- Traversal: `iterchildren()`, `getparent()`, `getprevious()`, `getnext()`.
- Search: `find()`, `findall()`.
- Serialization: `etree.tounicode(...)`, `etree.tostring(...)`.

## Proposed Adapter Surface
Minimal interface for a node wrapper (`HtmlNode`) and parser (`parse_html`).

```text
parse_html(html: str) -> HtmlDocument
HtmlDocument.root -> HtmlNode
HtmlNode.tag: str
HtmlNode.attrib: dict[str, str]
HtmlNode.text: str
HtmlNode.tail: str
HtmlNode.parent() -> HtmlNode | None
HtmlNode.children() -> list[HtmlNode]
HtmlNode.iterchildren() -> iterator[HtmlNode]
HtmlNode.find(selector: str) -> HtmlNode | None
HtmlNode.findall(selector: str) -> list[HtmlNode]
HtmlNode.getprevious() -> HtmlNode | None
HtmlNode.getnext() -> HtmlNode | None
HtmlNode.to_html() -> str
```

Notes:
- `tail` does not exist in justhtml; compute it from sibling text nodes where needed.
- `find/findall` should be CSS selectors (justhtml supports `query_selector*`).
- `to_html` used only in the table-unpack logic; can be deferred or replaced.

## Mapping: lxml -> Adapter -> justhtml
- `etree.HTML(html)` -> `parse_html(html)` -> `JustHTML(html)`
- `node.tag` -> `HtmlNode.tag` -> `node.name` (or `node.tag`)
- `node.attrib` -> `HtmlNode.attrib` -> `node.attrs` or `node.attributes`
- `node.text` -> `HtmlNode.text` -> `node.text` (text content)
- `node.tail` -> `HtmlNode.tail` -> computed from next sibling text nodes
- `node.iterchildren()` -> `HtmlNode.iterchildren()` -> iterate `node.children`
- `node.getparent()` -> `HtmlNode.parent()` -> `node.parent`
- `node.getprevious()` -> `HtmlNode.getprevious()` -> previous sibling
- `node.getnext()` -> `HtmlNode.getnext()` -> next sibling
- `node.findall('.//tr')` -> `HtmlNode.findall('tr')`

## Spike Implementation
See `src/html2latex/html_adapter.py` for a minimal wrapper that exposes the interface above.

## Next Steps (MOD-06)
- Wire adapter into `html2latex.py` and `utils/unpack_merged_cells_in_table.py`.
- Add tests to validate adapter behaviors (children order, parent/sibling links, text/tail).
- Replace XML-specific APIs with adapter-based traversal.
