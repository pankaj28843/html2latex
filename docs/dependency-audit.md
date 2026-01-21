# Dependency + External Tooling Audit

Date: 2026-01-21
Scope: html2latex modernization (Python 3 + justhtml)

## Python Dependencies (current)

### Runtime (`pyproject.toml`)
| Package | Constraint | Notes |
| --- | --- | --- |
| Jinja2 | >=3.1.6 | Template rendering engine. |
| html2text | >=2025.4.15 | HTML-to-text helpers. |
| justhtml | >=0.20.0 | HTML parsing adapter (replaces lxml). |
| pyenchant | >=3.3.0 (extra) | Optional spellcheck; requires system enchant. |

### Dependency groups
| Group | Packages | Notes |
| --- | --- | --- |
| test | pytest>=9.0.2 | Unit + golden tests. |
| lint | ruff>=0.14.11 | Lint/format checks. |
| demo | Flask>=3.1.2, redis>=7.1.0 | Demo app runtime. |
| e2e | playwright>=1.51.0 | Playwright smoke test. |

## External Tools / System Dependencies

| Tool | Where referenced | Status | Notes |
| --- | --- | --- | --- |
| enchant (system) | spellcheck extra | Optional | Required when using `spellcheck` extra. |
| tectonic | `tests/test_latex_validity.py` | Required | Used to compile LaTeX fixtures. |
| Playwright browsers | `tests/e2e/test_demo_smoke.py` | Optional | Install via `python -m playwright install`. |

## Observations
- Legacy requirements files have been removed; `pyproject.toml` + `uv.lock` are the source of truth.
- Legacy phantomjs/bower/screenshot tooling has been removed.

## Recommendations (priority)
1. Keep dependency groups minimal and documented.
2. Keep external tool requirements (tectonic, playwright) documented in `INSTALL.md`.
3. Periodically refresh `uv.lock` to keep constraints current.
