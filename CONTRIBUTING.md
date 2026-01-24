# Contributing

Thanks for helping improve HTML2LaTeX!

## Setup

- Python dependencies:
  - `uv sync --locked --group test --group lint`
- Tectonic (required for LaTeX validation):
  - Install the `tectonic` CLI and ensure it is on your PATH.
- Node.js (required for formatting):
  - Node 20+ recommended.

## Project structure

This project uses a **uv workspace** with two members:

- **html2latex** (root): The main library
- **html2latex-demo** (`demo-app/`): Demo web application

## Demo app development

The demo app has its own `pyproject.toml` in `demo-app/` and is a workspace member.

### Running with Docker

```bash
# Build and run
docker compose build
docker compose up -d

# Access at http://localhost:15005

# Development mode with hot reload (watches file changes)
docker compose watch
```

### Running locally (without Docker)

```bash
uv run --package html2latex-demo python demo-app/app.py
```

## File formatting

All HTML and LaTeX files in the project are formatted with Prettier for consistency and readability.

The project uses:
- **2-space indentation** (no tabs)
- **LF line endings**
- `prettier-plugin-latex` for LaTeX formatting

### Configuration

The `.prettierrc.json` configures both HTML and LaTeX formatting:
- `tabWidth: 2` - 2-space indentation
- `useTabs: false` - spaces, not tabs
- `plugins: ["prettier-plugin-latex"]` - enables LaTeX support

### Formatting all files

Install dependencies and format:

```bash
npm install --no-save prettier@3.3.3 prettier-plugin-latex@2.0.1
npx prettier --write "**/*.html" "**/*.tex"
```

### Check formatting

```bash
npx prettier --check "**/*.html" "**/*.tex"
```

Note: Error fixtures under `tests/fixtures/html2latex/errors/` are excluded via `.prettierignore`.

## Fixture LaTeX validation

All fixture `.tex` outputs should compile cleanly. Run the per-fixture check with:

```bash
HTML2LATEX_TEX_FIXTURES=1 uv run pytest tests/test_latex_validity.py -q
```

## Code quality

### Linting with Ruff

The project uses Ruff for linting and formatting with an expanded rule set:

- **Core**: E (pycodestyle errors), F (Pyflakes), W (pycodestyle warnings), I (isort)
- **Best practices**: UP (pyupgrade), B (bugbear), SIM (simplify), C4 (comprehensions)
- **Code quality**: C90 (complexity), A (builtins shadowing), PTH (pathlib)
- **Pylint subset**: PL (pylint), TRY (exception handling), PERF (performance)
- **Ruff-specific**: RUF, FURB (refurbished)

Run linting:

```bash
uv run ruff check .
uv run ruff format --check .
```

### Testing with Pytest

Tests use `importlib` import mode and strict settings:

```bash
# Run all tests with coverage
uv run pytest --cov=html2latex --cov-report=term-missing --cov-fail-under=100

# Run unit tests only
uv run pytest -m unit --no-cov

# Run with verbose output
uv run pytest -v
```

## Standard validation loop

```bash
uv run ruff check .
uv run ruff format --check .
npm install --no-save prettier@3.3.3 prettier-plugin-latex@2.0.1
npx prettier --check "**/*.html" "**/*.tex"
uv run pytest --cov=html2latex --cov-report=term-missing --cov-fail-under=100
HTML2LATEX_TEX_FIXTURES=1 uv run pytest tests/test_latex_validity.py -q
```

## Docker

The Docker setup uses best practices:

- **Multi-stage build**: Separate build and runtime stages for smaller images
- **Non-root user**: Runs as `appuser` for security
- **Healthchecks**: Both Dockerfile and docker-compose.yml include healthchecks
- **Redis**: Uses Redis 7 with healthcheck-based dependency management
