# Packaging Migration Notes

We have moved to `pyproject.toml` with `setuptools` and `uv` lockfiles.

Key points:
- The source layout remains `src/`.
- Templates are included via `[tool.setuptools.package-data]`.
- Old `setup.py` remains temporarily but is no longer required for install.
- Dependency groups are in `[dependency-groups]` (dev, test, lint, demo).

If you need to install in editable mode:

```bash
uv sync
```

Building artifacts:

```bash
uv build
```
