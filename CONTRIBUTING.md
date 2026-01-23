# Contributing

Thanks for helping improve HTML2LaTeX!

## Setup

- Python dependencies:
  - `uv sync --locked --group test --group lint`
- Tectonic (required for LaTeX validation):
  - Install the `tectonic` CLI and ensure it is on your PATH.
- Node.js (required for HTML fixture formatting):
  - Node 20+ recommended.
- tex-fmt (required for LaTeX fixture formatting):
  - Install from [GitHub releases](https://github.com/WGUNDERWOOD/tex-fmt/releases) or via `cargo install tex-fmt`

## Fixture formatting

### HTML fixtures

HTML fixtures are canonical inputs. Format them with Prettier before committing:

```bash
npx --yes prettier@3.3.3 --write "tests/fixtures/html2latex/**/*.html"
```

To check formatting without rewriting:

```bash
npx --yes prettier@3.3.3 --check "tests/fixtures/html2latex/**/*.html"
```

Note: error fixtures under `tests/fixtures/html2latex/errors/` are intentionally invalid and are excluded from Prettier formatting.
The Prettier config favors human readability (100-column width and CSS whitespace handling).

### LaTeX fixtures

LaTeX `.tex` fixtures are formatted with tex-fmt for readability. Format them before committing:

```bash
find tests/fixtures/html2latex -name "*.tex" -exec tex-fmt --config tex-fmt.toml {} \;
```

To check formatting without rewriting:

```bash
find tests/fixtures/html2latex -name "*.tex" -exec tex-fmt --check --config tex-fmt.toml {} +
```

The `tex-fmt.toml` configuration disables line wrapping and uses 2-space indentation.

## Fixture LaTeX validation

All fixture `.tex` outputs should compile cleanly. Run the per-fixture check with:

```bash
HTML2LATEX_TEX_FIXTURES=1 uv run pytest tests/test_latex_validity.py -q
```

## Standard validation loop

```bash
uv run ruff check .
uv run ruff format --check .
npx --yes prettier@3.3.3 --check "tests/fixtures/html2latex/**/*.html"
find tests/fixtures/html2latex -name "*.tex" -exec tex-fmt --check --config tex-fmt.toml {} +
uv run pytest --cov=html2latex --cov-report=term-missing --cov-fail-under=100
HTML2LATEX_TEX_FIXTURES=1 uv run pytest tests/test_latex_validity.py -q
```
