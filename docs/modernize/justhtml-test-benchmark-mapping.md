# JustHTML Test + Benchmark Inspiration Mapping (Step 0.4)

Date: 2026-01-21
Scope: Map JustHTML harness/bench patterns to html2latex tests and benchmarks

## Summary
JustHTML separates concerns into: (1) data-driven fixtures + harness runner, (2) a compact regression summary file, and (3) standalone benchmark scripts. This mapping proposes a similar structure for html2latex, adapted to LaTeX output validation and WYSIWYG HTML coverage.

## JustHTML patterns worth adopting
- External fixtures (html5lib-tests) kept out of repo, symlinked locally.
- Harness runner that aggregates per-file stats and writes a `test-summary.txt` baseline.
- Regression checker that diffs current failures vs the baseline and exits non-zero.
- Data-driven fixtures for correctness and coverage hot spots.
- Benchmarks separated by intent: `performance.py` (dataset throughput), `profile.py` (cProfile), `correctness.py` (suite compliance).

## html2latex adaptation plan
### 1) Data-driven fixture harness
- Keep current JSON golden tests but add a small harness wrapper that:
  - Normalizes output, records pass/fail per case.
  - Writes a per-file summary for fixtures (mirrors JustHTML `test-summary.txt`).
  - Optionally diffs against baseline summary to detect regressions.
- Keep pytest as the runner; add a dedicated `tests/harness/` with:
  - `reporter.py` (summary + pattern output)
  - `regressions.py` (baseline diff against `test-summary.txt`)
  - `runner.py` (fixture loader + result collection)

### 2) Regression summary format
- Use a simplified summary that matches JustHTML's pattern semantics:
  - `.` = pass
  - `x` = fail
  - `s` = skip
- Keep baseline at repo root: `test-summary.txt` (git-tracked).
- Add `python -m tests.harness.regressions` (or pytest hook) to fail CI on new regressions.

### 3) Benchmarks layout
- Add `benchmarks/` to mirror JustHTML:
  - `benchmarks/performance.py`: throughput + RSS sampling on a representative HTML corpus.
  - `benchmarks/profile.py`: cProfile on large HTML samples.
  - `benchmarks/correctness.py`: optional comparator harness vs a reference LaTeX output set.
- Prefer a small, versioned fixture corpus (no large datasets in repo). If needed, allow optional external corpora with environment variables.

### 4) WYSIWYG tag coverage fixtures
Create a fixture matrix for common editor outputs (HTML subset). Proposed tags/constructs:
- Text + inline: `p`, `br`, `span`, `strong`, `em`, `u`, `s`, `sub`, `sup`, `code`, `kbd`.
- Structure: `div`, `blockquote`, `hr`, headings `h1`-`h6`.
- Lists: `ul/ol/li`, nested lists, checklists (data attributes).
- Links + media: `a`, `img` (local + remote), `figure/figcaption`.
- Tables: `table/thead/tbody/tfoot/tr/th/td`, `colgroup/col`.
- Semantics: `pre`, `textarea`, `abbr`, `cite` (as supported by templates).

Each fixture should include:
- HTML input
- Expected LaTeX output (golden)
- Optional metadata: `skip`, `xfail`, `features` (e.g., `tables`, `images`)

### 5) Coverage hot-spot tests
Mirror JustHTML's targeted edge tests by adding a `tests/unit/hotspots/` suite for:
- Table width heuristics
- Image sizing and alignment
- Escaping and LaTeX injection prevention
- Line separator normalization

## Proposed file layout
```
benchmarks/
  performance.py
  profile.py
  correctness.py

tests/
  harness/
    __init__.py
    reporter.py
    regressions.py
    runner.py
  fixtures/
    wysiwyg/
      basic.json
      lists.json
      tables.json
      media.json
    regressions/
      known-issues.json
  golden/
    cases.json
  unit/
    hotspots/
```

## CI integration ideas
- Add a regression check step that runs only on full test runs.
- Store `test-summary.txt` in repo root; update intentionally when behavior changes.
- Allow `pytest -m regression` to run only summary-diff checks.

## Open decisions
- Whether to keep the existing `tests/golden/cases.json` as the baseline or split into smaller files by category.
- Whether to include a small on-repo HTML corpus for benchmarks or require external data.
- Whether to add a lightweight CLI wrapper (similar to `run_tests.py`) for local regression runs.
