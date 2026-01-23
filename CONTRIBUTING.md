# Contributing

Thanks for helping improve HTML2LaTeX!

## Setup

- Python dependencies:
  - `uv sync --locked --group test --group lint`
- Tectonic (required for LaTeX validation):
  - Install the `tectonic` CLI and ensure it is on your PATH.
- Node.js (required for HTML and LaTeX formatting):
  - Node 20+ recommended.

## File formatting

All HTML and LaTeX files in the project are formatted for consistency and readability.

### HTML files

Format all HTML files with Prettier before committing:

```bash
npx --yes prettier@3.3.3 --write "**/*.html"
```

To check formatting without rewriting:

```bash
npx --yes prettier@3.3.3 --check "**/*.html"
```

Note: Error fixtures under `tests/fixtures/html2latex/errors/` are excluded via `.prettierignore`.
The Prettier config favors human readability (100-column width and CSS whitespace handling).

### LaTeX files

Format all `.tex` files with unified-latex before committing:

```bash
find . -name "*.tex" -not -path "./node_modules/*" -not -path "./.venv/*" -exec sh -c 'npx --yes @unified-latex/unified-latex-cli@1.8.3 "$1" -o "$1" --no-stdout 2>/dev/null' _ {} \;
```

unified-latex provides intelligent LaTeX formatting that:
- Indents environments properly (itemize, enumerate, etc.)
- Adds line breaks after section commands
- Preserves verbatim blocks
- Works with LaTeX fragments (no document class required)

## Fixture LaTeX validation

All fixture `.tex` outputs should compile cleanly. Run the per-fixture check with:

```bash
HTML2LATEX_TEX_FIXTURES=1 uv run pytest tests/test_latex_validity.py -q
```

## Standard validation loop

```bash
uv run ruff check .
uv run ruff format --check .
npx --yes prettier@3.3.3 --check "**/*.html"
uv run pytest --cov=html2latex --cov-report=term-missing --cov-fail-under=100
HTML2LATEX_TEX_FIXTURES=1 uv run pytest tests/test_latex_validity.py -q
```
