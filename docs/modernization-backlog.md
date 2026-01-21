# HTML2LaTeX Modernization Backlog (Python 3 + justhtml)

Date: 2026-01-21
Owner: html2latex core team

## Executive Summary
Modernize html2latex to the latest stable Python 3, replace lxml with justhtml across the parsing stack, adopt uv + ruff + pytest, and add GitHub Actions CI/CD. Port the demo app to Python 3 to remain a living integration test and reference UI.

## Decisions (Locked)
- Primary runtime: latest stable Python 3 minor (3.14.x as of 2026-01-21).
- Minimum runtime: Python >= 3.10 (required by justhtml).
- HTML parsing: justhtml only; lxml removed entirely.
- Tests: pytest (no nose), golden fixtures for output stability.
- Tooling: uv for env + lockfile, ruff for lint/format.
- Demo app: port to Python 3 (Flask + redis).

## Architecture Principles
- Dependency inversion: parsing is behind an adapter interface; core conversion does not know the parser implementation.
- Functional core, imperative shell: parsing + IO at edges; HTML-to-LaTeX transformation is pure and testable.
- Single responsibility: parsing, transform, rendering, and IO separated.
- Stable public API: `html2latex(html, **kwargs)` remains backward compatible where possible.
- Output stability: regressions detected via golden fixtures; changes require explicit approval.

## Target Architecture (High-level)
- `html2latex/adapter/html.py`: Parser adapter (justhtml). Provides DOM node abstraction with:
  - `tag`, `text`, `tail`, `attrib`, `children`, `parent`, `comments`.
  - Selector helpers for table logic.
- `html2latex/core/transform.py`: Pure transform functions (node -> LaTeX fragment).
- `html2latex/templates/`: Jinja templates (unchanged content unless required).
- `html2latex/html2latex.py`: Orchestration glue calling adapter + core.

Data flow: HTML string -> parse -> DOM -> transform -> LaTeX string.

## Non-goals
- Rewriting LaTeX templates or expanding HTML feature coverage.
- Introducing new rendering engines or PDF generation pipeline.
- Supporting Python < 3.10.

## TODO List (maps to issues)
- [ ] MOD-00 Dependency + external tooling audit (#41)
- [ ] MOD-01 Decide Python support matrix + policy (#20)
- [ ] MOD-02 justhtml adapter design + spike (#21)
- [ ] MOD-03 Golden fixture corpus (#22)
- [ ] MOD-04 Move to `pyproject.toml` + uv (#23)
- [ ] MOD-05 Python 3 compatibility sweep (#24)
- [ ] MOD-06 Replace lxml with justhtml (adapter + refactor) (#25)
- [ ] MOD-07 Remove legacy git dependency or inline required functionality (#26)
- [ ] MOD-08 Upgrade dependencies (Jinja, html2text, pyenchant) (#27)
- [ ] MOD-09 Jinja environment modernization (#28)
- [ ] MOD-10 Retire legacy install hooks/external tooling (#29)
- [ ] MOD-11 Migrate tests from nose to pytest (#30)
- [ ] MOD-12 Golden regression tests (HTML -> LaTeX) (#31)
- [ ] MOD-13 Ruff lint + format (#32)
- [ ] MOD-14 GitHub Actions CI (#33)
- [ ] MOD-15 GitHub Actions CD (#34)
- [ ] MOD-16 Docs update (README/INSTALL) (#35)
- [ ] MOD-17 Demo app port to Python 3 (#36)
- [ ] MOD-18 Output parity review + performance check (#37)

## Issue Index

| Key | Issue | Link |
| --- | ----- | ---- |
| MOD-00 | Dependency + external tooling audit | https://github.com/pankaj28843/html2latex/issues/41 |
| MOD-01 | Decide Python support matrix + version policy | https://github.com/pankaj28843/html2latex/issues/20 |
| MOD-02 | justhtml adapter design + spike | https://github.com/pankaj28843/html2latex/issues/21 |
| MOD-03 | Golden fixture corpus | https://github.com/pankaj28843/html2latex/issues/22 |
| MOD-04 | Move to pyproject.toml + uv | https://github.com/pankaj28843/html2latex/issues/23 |
| MOD-05 | Python 3 compatibility sweep | https://github.com/pankaj28843/html2latex/issues/24 |
| MOD-06 | Replace lxml with justhtml (adapter + refactor) | https://github.com/pankaj28843/html2latex/issues/25 |
| MOD-07 | Remove legacy git dependency or inline functionality | https://github.com/pankaj28843/html2latex/issues/26 |
| MOD-08 | Upgrade dependencies (Jinja, html2text, pyenchant) | https://github.com/pankaj28843/html2latex/issues/27 |
| MOD-09 | Jinja environment modernization | https://github.com/pankaj28843/html2latex/issues/28 |
| MOD-10 | Retire legacy install hooks/external tooling | https://github.com/pankaj28843/html2latex/issues/29 |
| MOD-11 | Migrate tests from nose to pytest | https://github.com/pankaj28843/html2latex/issues/30 |
| MOD-12 | Golden regression tests (HTML -> LaTeX) | https://github.com/pankaj28843/html2latex/issues/31 |
| MOD-13 | Ruff lint + format | https://github.com/pankaj28843/html2latex/issues/32 |
| MOD-14 | GitHub Actions CI | https://github.com/pankaj28843/html2latex/issues/33 |
| MOD-15 | GitHub Actions CD | https://github.com/pankaj28843/html2latex/issues/34 |
| MOD-16 | Docs update (README/INSTALL) | https://github.com/pankaj28843/html2latex/issues/35 |
| MOD-17 | Demo app port to Python 3 | https://github.com/pankaj28843/html2latex/issues/36 |
| MOD-18 | Output parity review + performance check | https://github.com/pankaj28843/html2latex/issues/37 |

## GitHub Issue Backlog (detailed)

### MOD-01 — Decide Python support matrix + version policy
Goal: Lock the supported Python versions and publishing policy.
Tasks:
- Confirm primary runtime (3.14.x) and minimum version (>=3.10).
- Update `.python-version`, classifiers, and docs.
- Define CI matrix policy for supported versions.
Acceptance:
- Policy documented in README + pyproject classifiers.
- CI matrix aligned to policy.
Depends on: None
Blocks: MOD-04, MOD-14, MOD-15, MOD-16, MOD-17

### MOD-02 — justhtml adapter design + spike
Goal: Replace lxml with justhtml via a stable adapter boundary.
Tasks:
- Review justhtml API (selector + node access).
- Map lxml usage patterns to adapter methods.
- Spike a minimal adapter for tag/text/attrib/children.
Acceptance:
- Adapter interface documented + spike committed.
Depends on: None
Blocks: MOD-06

### MOD-03 — Golden fixture corpus
Goal: Establish baseline outputs for regression detection.
Tasks:
- Collect representative HTML inputs (lists, tables, math spans, images).
- Capture current LaTeX outputs as fixtures.
- Define normalization rules (whitespace, line endings).
Acceptance:
- Fixture set committed under `tests/golden/`.
Depends on: None
Blocks: MOD-12, MOD-18

### MOD-04 — Move to `pyproject.toml` + uv
Goal: Modern packaging and reproducible dependency management.
Tasks:
- Create `pyproject.toml` with PEP 621 metadata.
- Define dependency groups (dev/test/demo).
- Generate and commit `uv.lock`.
Acceptance:
- `uv lock` and `uv build` succeed.
Depends on: MOD-01
Blocks: MOD-08, MOD-11, MOD-13, MOD-14, MOD-15

### MOD-05 — Python 3 compatibility sweep
Goal: Make code run on Python 3 before parser swap.
Tasks:
- Replace HTMLParser/htmlentitydefs/unichr/iteritems/print.
- Fix bytes/str boundaries.
- Update unicode handling and tests.
Acceptance:
- Core module imports and basic conversion works on Python 3.
Depends on: MOD-01
Blocks: MOD-06, MOD-11

### MOD-06 — Replace lxml with justhtml (adapter + refactor)
Goal: Eliminate lxml entirely.
Tasks:
- Implement adapter methods for required DOM ops.
- Rewrite table/unpack logic without lxml APIs.
- Replace `etree` usage in core.
Acceptance:
- No lxml dependency; fixtures match or diffs are documented.
Depends on: MOD-02, MOD-05
Blocks: MOD-12, MOD-18

### MOD-07 — Remove legacy git dependency or inline functionality
Goal: Remove git dependency and reduce fragility.
Tasks:
- Locate `check_if_html_has_text` usage.
- Implement equivalent local function with tests.
Acceptance:
- No git dependency in pyproject.
Depends on: MOD-05
Blocks: MOD-04, MOD-08

### MOD-08 — Upgrade dependencies (Jinja, html2text, pyenchant)
Goal: Modernize runtime deps and capture system requirements.
Tasks:
- Select supported versions compatible with Python 3.14.
- Make spellcheck optional extra if system libs required.
- Update code for any API changes.
Acceptance:
- `uv lock` resolves cleanly; optional extras documented.
Depends on: MOD-04, MOD-07
Blocks: MOD-09

### MOD-09 — Jinja environment modernization
Goal: Explicit, predictable template rendering.
Tasks:
- Configure Environment (loader, autoescape, trimming flags).
- Validate template rendering behavior with fixtures.
Acceptance:
- Templates render consistently across Python versions.
Depends on: MOD-08
Blocks: MOD-12, MOD-18

### MOD-10 — Retire legacy install hooks/external tooling
Goal: Eliminate install-time `sudo` and obsolete tooling.
Tasks:
- Remove custom `setup.py` install command.
- Replace phantomjs/bower path with optional feature flags.
Acceptance:
- Clean install with no global side effects.
Depends on: MOD-04
Blocks: MOD-16

### MOD-11 — Migrate tests from nose to pytest
Goal: Standardize testing on pytest.
Tasks:
- Convert nose config to pytest config in pyproject.
- Update test discovery and assertions.
Acceptance:
- `uv run pytest` green.
Depends on: MOD-04, MOD-05
Blocks: MOD-12, MOD-14

### MOD-12 — Golden regression tests (HTML -> LaTeX)
Goal: Lock output stability.
Tasks:
- Create test harness for golden fixtures.
- Add normalization and diff reporting.
Acceptance:
- Golden tests pass on all supported versions.
Depends on: MOD-03, MOD-06, MOD-09, MOD-11
Blocks: MOD-18

### MOD-13 — Ruff lint + format
Goal: Adopt ruff for lint/format across the repo.
Tasks:
- Add ruff config to pyproject.
- Fix lint violations and format code.
Acceptance:
- `ruff check .` and `ruff format --check .` pass.
Depends on: MOD-04
Blocks: MOD-14

### MOD-14 — GitHub Actions CI
Goal: CI for tests + lint on PRs.
Tasks:
- Add CI workflow using `setup-python` + uv.
- Cache dependencies where safe.
- Run ruff + pytest.
Acceptance:
- CI green on PRs.
Depends on: MOD-01, MOD-04, MOD-11, MOD-13
Blocks: MOD-15

### MOD-15 — GitHub Actions CD
Goal: Build and publish artifacts on release/tag.
Tasks:
- Add release workflow with `uv build`.
- Upload artifacts to GitHub Releases.
Acceptance:
- Release pipeline produces sdist/wheel artifacts.
Depends on: MOD-04, MOD-14
Blocks: None

### MOD-16 — Docs update (README/INSTALL)
Goal: Update docs for Python 3 + uv + justhtml.
Tasks:
- Rewrite setup/usage sections.
- Add CI badge and new dependency notes.
- Document removal of lxml + deprecated tools.
Acceptance:
- Docs match actual workflow.
Depends on: MOD-01, MOD-04, MOD-10
Blocks: None

### MOD-17 — Demo app port to Python 3
Goal: Keep demo app as working integration test.
Tasks:
- Update Flask + redis deps.
- Fix hmac usage for Python 3 (bytes + digestmod).
- Add uv dev group for demo app.
Acceptance:
- Demo app runs under Python 3; conversion endpoint works.
Depends on: MOD-01, MOD-04, MOD-05
Blocks: MOD-16

### MOD-18 — Output parity review + performance check
Goal: Validate output changes and runtime performance.
Tasks:
- Compare golden outputs across versions.
- Document intentional diffs.
- Run basic perf baseline (large HTML inputs).
Acceptance:
- Parity report committed; diffs approved.
Depends on: MOD-12
Blocks: None

## Execution Order (Critical Path)
1. MOD-01
2. MOD-02, MOD-03
3. MOD-04, MOD-05
4. MOD-06
5. MOD-07, MOD-08, MOD-09
6. MOD-10, MOD-11, MOD-12
7. MOD-13
8. MOD-14, MOD-15
9. MOD-17
10. MOD-16, MOD-18

## References
- uv projects + lock/sync: https://docs.astral.sh/uv/guides/projects/
- uv lock/sync: https://docs.astral.sh/uv/concepts/projects/sync/
- uv project layout: https://docs.astral.sh/uv/concepts/projects/layout/
- Ruff configuration: https://docs.astral.sh/ruff/configuration/
- pytest configuration: https://docs.pytest.org/en/stable/reference/customize.html
- pytest good practices: https://docs.pytest.org/en/stable/explanation/goodpractices.html
- Jinja Environment API: https://jinja.palletsprojects.com/en/stable/api/
- GitHub Actions workflow syntax: https://docs.github.com/en/actions/automating-your-workflow-with-github-actions/workflow-syntax-for-github-actions/
- GitHub Actions Python build/test: https://docs.github.com/en/actions/tutorials/build-and-test-code/python/
- GitHub Actions caching: https://docs.github.com/en/actions/using-workflows/caching-dependencies-to-speed-up-workflows/
- JustHTML docs: https://justhtml.readthedocs.io/en/latest/
- Python release history: https://www.python.org/downloads/
