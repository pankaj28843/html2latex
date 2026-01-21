# Architecture Audit (Step 0.1)

Date: 2026-01-21
Scope: html2latex core pipeline + adapters + templates

## High-level pipeline
1. `html2latex(html, **kwargs)`
   - Strips input, early-exits on empty, then normalizes HTML via `fix_encoding_of_html_using_lxml()`.
2. `fix_encoding_of_html_using_lxml(html)`
   - Now uses `parse_html()` (JustHTML) and `to_html()` to normalize HTML, then trims outer `<p>` if not present in original input.
3. `_html2latex(html, **kwargs)`
   - `parse_html(html)` → `HtmlDocument` → selects `.//body` (or root) → iterates children.
4. `delegate(element, **kwargs)`
   - Dispatches by tag to specialized classes (`H1`, `Table`, `IMG`, etc.) or `HTMLElement`.
5. `HTMLElement.render()` and subclasses
   - Uses Jinja templates in `src/html2latex/templates/*.tex` to produce LaTeX.

## Module map
- `src/html2latex/html2latex.py`
  - Central pipeline, tag dispatch, Jinja env, and most transformation logic.
  - Many regex-based post-processing steps in `_html2latex`.
- `src/html2latex/html_adapter.py`
  - Thin adapter over JustHTML to emulate lxml-like node API.
- `src/html2latex/templates/*.tex`
  - Jinja templates that render LaTeX fragments by tag.
- `src/html2latex/utils/*`
  - Inline style parsing, LaTeX escaping, spellchecking, image size reading, table cell unpacking.

## Global state + side effects
- Global Jinja `texenv` and `FileSystemLoader` created at import time.
- `logging.basicConfig(...)` invoked at import time (affects global logging).
- Global constants: `VERSION`, `CAPFIRST_ENABLED`.
- Image handling (`IMG`):
  - Downloads remote images via `wget` into `/var/tmp/html2latex-remote-images`.
  - Converts grayscale using ImageMagick `convert` into `/tmp` and `/var/tmp`.
  - Uses subprocesses (`Popen`) and filesystem side effects.
- Template render includes conditional logic for base64 encoding and optional alignment.

## Thread-safety considerations (current)
- Global Jinja environment may be shared across threads; templates are loaded globally.
- Global mutable state: `CAPFIRST_ENABLED` used in `HTMLElement.cap_first`.
- Shared temp directories for images; concurrent processes could collide on filenames.
- Subprocess calls are not synchronized; `wget`/`convert` may race on same path.

## Performance hotspots (observed)
- Multiple `re.sub` passes in `_html2latex` for cleanup and formatting.
- Table handling (`Table`, `TD`, `TR`) does per-cell computations and merges.
- `delegate()` dispatch is a long if/elif chain; repeated attribute lookups and conversions.

## Test surface (current)
- Unit tests cover html2latex core, adapter, text processing, images, and integration flows.
- LaTeX validity uses tectonic (required).
- Playwright E2E covers demo app.

## Immediate opportunities
- Introduce a parser/transform/render split with explicit interfaces (align with JustHTML pattern).
- Centralize error taxonomy (codes + locations) across parse → transform → render.
- Replace global env with injectable environment factory (improves thread-safety).
- Formalize image I/O as an adapter with pluggable downloader/transformer.
- Add benchmark harness + regression summary (JustHTML test-summary style).
