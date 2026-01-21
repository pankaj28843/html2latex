# Installation

## Python 3 + uv (recommended)

```bash
uv sync
```

Optional spellcheck support (requires the system `enchant` library):

```bash
uv sync --extra spellcheck
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
