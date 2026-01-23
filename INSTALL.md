# Installation

## Python 3 + uv (recommended)

```bash
uv sync
```

## Editable install

```bash
uv sync
```

## Demo app

The demo app is a workspace member with its own dependencies.

### With Docker (recommended)

```bash
docker compose build
docker compose up -d
# Access at http://localhost:15005

# Development mode with hot reload
docker compose watch
```

### Without Docker

```bash
uv sync --all-packages
uv run --package html2latex-demo python demo-app/app.py
```

## LaTeX validity (requires `tectonic`)

Install `tectonic` and run the LaTeX validity test:

```bash
curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.fullyjustified.net | sh
sudo install -m 755 tectonic /usr/local/bin/tectonic
```

```bash
uv run pytest tests/test_latex_validity.py -q
```

## Playwright E2E (optional)

```bash
uv sync --group test --group e2e --all-packages
uv run python -m playwright install --with-deps chromium
uv run pytest tests/e2e/test_demo_smoke.py -q
```
