# Benchmarking Harness Design (Step 0.6)

Date: 2026-01-21
Scope: Performance + memory benchmarking for html2latex

## Goals
- Establish a reproducible baseline for throughput and memory.
- Detect regressions when refactoring core pipeline.
- Keep benchmarks opt-in for CI (run locally or nightly).

## Proposed benchmark layout
```
benchmarks/
  data/
    small/
      simple.html
      wysiwyg-basic.html
    medium/
      newsletter.html
      docs.html
  performance.py
  profile.py
  memory.py
  README.md
```

## Datasets
- **Small (on repo)**: minimal HTML cases, WYSIWYG-like structures, tables and images.
- **Medium (on repo)**: a handful of representative documents (sanitized, no PII).
- **Large (optional external)**: configurable via env var `HTML2LATEX_BENCH_DIR`.

## Benchmarks
### `performance.py`
- Measure wall-clock time for `html2latex` on each dataset.
- Use `time.perf_counter` and repeat N times (default 5).
- Report:
  - mean, p50, p95
  - throughput (docs/sec)

### `memory.py`
- Use `tracemalloc` and optional `psutil` (if installed).
- Capture peak and delta RSS for each dataset.
- Report:
  - `rss_start_mb`, `rss_peak_mb`, `rss_delta_mb`
  - `tracemalloc` top N allocations by file/line

### `profile.py`
- cProfile capture for a representative medium case.
- Output `.pstats` and a human-readable summary.

## Benchmark CLI behavior
- `uv run python benchmarks/performance.py --repeat 5 --dataset small`
- `uv run python benchmarks/memory.py --dataset medium`
- `uv run python benchmarks/profile.py --case docs.html`

## Reporting format
- Print JSON lines for machine parsing.
- Example per-case output:
  - `{ "case": "small/simple.html", "mean_ms": 3.2, "p95_ms": 3.9, "docs_per_sec": 300 }`

## CI integration (optional)
- Keep benchmarks out of default CI due to variance.
- Add a manual workflow or scheduled run to compare against baseline JSON.
- Gate only on large regressions (configurable threshold, e.g., 20% slower).

## Dependency notes
- `psutil` optional: only used for RSS if installed.
- `tracemalloc` is stdlib and always available.

## Open questions
- Should we commit baseline benchmark JSON or keep it in artifacts?
- Do we want to run a small benchmark subset in PR CI?

