# HTML2LaTeX

![CI](https://github.com/pankaj28843/html2latex/actions/workflows/ci.yml/badge.svg)

HTML2LaTeX converts WYSIWYG HTML fragments into LaTeX. The pipeline is built on
`justhtml`, typed ASTs, and deterministic serialization to produce reliable
output suitable for PDFs and reports.

## Highlights

- WYSIWYG tag coverage: headings (`h1`-`h3`), paragraphs/divs, lists (`ul/ol/dl`),
  tables (`thead/tbody/tfoot`, `th/td`, `colspan`), blockquotes, and `pre` blocks.
- Inline styles: bold/italic/underline/code/sup/sub.
- Links + images with package inference (`hyperref`, `graphicx`).
- Math passthrough via `<span class="math-tex">` or `data-latex` attributes.
- Thread-safe, immutable options with diagnostics when parsing is invalid.

## Requirements

- Python 3.10+
- Dependencies managed with `uv` via `pyproject.toml`

## Quick Start

```bash
uv sync
```

```bash
uv run python - <<'PY'
from html2latex.html2latex import html2latex

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
from html2latex.html2latex import html2latex

html = """
<p>Hello <strong>World</strong></p>
<p>Inline math: <span class="math-tex">\( x^2 + y^2 = z^2 \)</span></p>
"""

fragment = html2latex(html)
print(fragment)
```

### Convert HTML and inspect packages/diagnostics

```python
from html2latex.api import convert
from html2latex.models import ConvertOptions

options = ConvertOptions(strict=False)
result = convert("<a href='https://example.com'>Link</a>", options=options)

print(result.body)       # LaTeX fragment
print(result.packages)   # e.g., ("hyperref",)
print(result.diagnostics)
```

### Render a full LaTeX document

```python
from html2latex.html2latex import render

print(render("<p>Full document</p>"))
```

To add preamble content:

```python
from html2latex.api import convert
from html2latex.models import ConvertOptions
from html2latex.jinja import render_document

options = ConvertOptions(metadata={"preamble": "\\usepackage{amsmath}"})
result = convert("<p>Math</p>", options=options)
print(render_document(result.body, preamble=result.preamble))
```

## LaTeX Packages

Package requirements are inferred from the output. If you need a full document,
use `render()` or `render_document()` and include `result.preamble`.

Common packages:

- `hyperref` (links)
- `graphicx` (images)

## Demo App

A demo Flask app with a rich text editor is available:

```bash
docker compose build
docker compose up
```

Visit <http://127.0.0.1:15005/>.

## History

The original implementation (2014-2016) powered the
[ClassKlap](https://www.classklap.com) publishing workflow. The library targets
Python 3 and general-purpose use; the Xamcheck brand has been retired.

## CI

CI runs `ruff` (lint + format) and `pytest` across the supported Python matrix,
plus LaTeX validity checks (Tectonic) and Playwright E2E smoke tests.

## License

MIT License - see [LICENSE](LICENSE).
