# Dependency Alignment Audit (Step 0.2)

Date: 2026-01-21
Scope: Python 3, uv, Ruff, pytest, Jinja, Playwright, LaTeX tooling

## Python + uv
- `project.requires-python = ">=3.10"` (aligned with uv guidance to set version requirement).
- `uv.lock` is the source of truth; CI uses `uv sync --locked` to enforce determinism.
- Dependency groups (PEP 735): `test`, `lint`, `demo`, `e2e`, `dev` defined.
- Actionable: consider documenting `uv lock --check` and `uv sync --frozen` in CONTRIBUTING/CI notes for stricter lock validation.

## Ruff (lint + format)
- Config in `pyproject.toml` via `[tool.ruff]` (supported by Ruff docs).
- `target-version = "py310"` matches minimum supported Python.
- `extend-exclude = ["demo-app"]` excludes demo app code.
- Actionable (per Ruff settings docs): consider `force-exclude = true` if using pre-commit or if explicit paths are passed in CI to enforce exclusions.

## pytest
- `testpaths = ["tests"]` set in `pyproject.toml`.
- Coverage enforced in CI via `pytest --cov --cov-fail-under=90`.
- Actionable: define custom markers for e2e/latex/perf to allow `-m` targeting and reduce unnecessary runs.

## Jinja
- Environment configured in `setup_texenv()` with custom delimiters; `autoescape=False` (expected for LaTeX), `trim_blocks/lstrip_blocks=False` to preserve whitespace.
- Actionable: document Jinja environment policy (autoescape + whitespace rules) and ensure templates avoid raw LaTeX injection.

## Playwright
- CI installs browsers and runs a single smoke test.
- Actionable: add `pytest.ini` or `pyproject.toml` markers/config for Playwright (e.g., `-m e2e`), and document how to run headed or multi-browser locally.

## LaTeX tooling
- CI uses `tectonic` exclusively for validity checks.
- Actionable: document `tectonic` installation in `INSTALL.md` (already present); consider verifying local checks before PRs.

## Gaps / Proposed fixes
- Optional: add Ruff `force-exclude` and `lint.per-file-ignores` if needed for generated files.
- Optional: add `pytest` markers for e2e/latex/perf and configure `-m` defaults.
- Optional: add a short `docs/modernize/tooling.md` to consolidate uv/ruff/pytest/Jinja usage.
