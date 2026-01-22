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

```bash
uv sync --group demo
uv run python demo-app/app.py
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
uv sync --group test --group demo --group e2e
uv run python -m playwright install --with-deps chromium
uv run pytest tests/e2e/test_demo_smoke.py -q
```
