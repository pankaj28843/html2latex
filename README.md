# HTML2LaTeX

![CI](https://github.com/pankaj28843/html2latex/actions/workflows/ci.yml/badge.svg)

HTML2LaTeX converts WYSIWYG HTML fragments into LaTeX. The pipeline is built on
`justhtml`, typed ASTs, and deterministic serialization to produce reliable
output suitable for PDFs and reports.

## Highlights

- **Block elements**: headings (`h1`-`h5`), paragraphs, divs, lists (`ul`/`ol`/`dl`),
  blockquotes, `pre` blocks, `hr`, `figure`/`figcaption`, and semantic containers.
- **Tables**: Full support including `thead`/`tbody`/`tfoot`, `th`/`td`, `colspan`,
  `rowspan` (via `\multirow`), cell alignment (via `align` attribute or CSS `text-align`),
  and `caption`.
- **Inline formatting**: bold, italic, underline, code, superscript, subscript,
  strikethrough (`del`/`s`/`strike`), highlighted text (`mark`), font sizes (`small`/`big`),
  inline quotes (`q` with proper nesting), and semantic tags (`kbd`, `samp`, `var`, `cite`, `ins`).
- **Links and images**: `\href`/`\url` for links, `\includegraphics` for images with
  `width`/`height` attribute support.
- **Math passthrough**: via `<span class="math-tex">`, `data-latex`, or `data-math` attributes.
- **Text alignment**: `text-align` CSS on `p`/`div` maps to `center`/`flushleft`/`flushright`.
- **Thread-safe**: Immutable options with diagnostics for invalid input.

## Requirements

- Python 3.10+
- Dependencies managed with `uv` via `pyproject.toml`

## Quick Start

```bash
uv sync
```

```bash
uv run python - <<'PY'
from html2latex import html2latex

print(html2latex("<p>Hello World</p>"))
PY
```

Expected output (fragment):

```
Hello World\par
```

## Usage

### Convert HTML to a LaTeX fragment

```python
from html2latex import html2latex

html = """
<p>Hello <strong>World</strong></p>
<p>Inline math: <span class="math-tex">\( x^2 + y^2 = z^2 \)</span></p>
"""

fragment = html2latex(html)
print(fragment)
```

### Convert HTML and inspect packages/diagnostics

```python
from html2latex import Converter, ConvertOptions

converter = Converter(ConvertOptions(strict=False))
result = converter.convert("<a href='https://example.com'>Link</a>")

print(result.body)       # LaTeX fragment
print(result.packages)   # e.g., ("hyperref",)
print(result.diagnostics)
```

### Render a full LaTeX document

```python
from html2latex import render

print(render("<p>Full document</p>"))
```

To add preamble content:

```python
from html2latex import render, ConvertOptions

options = ConvertOptions(metadata={"preamble": "\\usepackage{amsmath}"})
print(render("<p>Math</p>", options=options))
```

## LaTeX Packages

Package requirements are inferred from the output. If you need a full document,
use `render()` or `render_document()` and include `result.preamble`.

Common packages:

- `hyperref` (links)
- `graphicx` (images)
- `xcolor` (highlighted text via `mark`)
- `ulem` (strikethrough via `del`/`s`/`strike`)
- `multirow` (table cells spanning multiple rows)

## Demo App

A demo Flask app with a rich text editor is available:

```bash
docker compose build
docker compose up
```

Visit <http://127.0.0.1:15005/>.

## History

The original implementation (2014-2016) powered the ClassKlap publishing
workflow. This version targets Python 3.10+ and general-purpose use.

## CI

CI runs `ruff` (lint + format) and `pytest` (465 tests, 100% coverage) across
Python 3.10-3.14, plus LaTeX validity checks (Tectonic) and Playwright E2E
smoke tests.

## License

MIT License - see [LICENSE](LICENSE).
