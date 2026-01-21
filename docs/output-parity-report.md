# Output Parity & Performance Report

Date: 2026-01-21
Scope: html2latex modernization (Python 3 + justhtml)

## Golden Fixture Parity

- Status: PASS
- Command: `uv run pytest tests/test_golden.py`
- Result: 5/5 cases passed
- Notes: Output normalization trims trailing whitespace. No intentional diffs recorded for current cases.

## Performance Snapshot

Heuristic: basic conversion runtime on a small, representative HTML input. This is not a formal benchmark.

- Command:
  - `uv run python - <<'PY'`
    `from html2latex.html2latex import html2latex`
    `html = "<p>Hello <b>World</b></p>" * 200`
    `for _ in range(200):`
    `    html2latex(html)`
    `print("ok")`
    `PY`
- Result: Completed without errors on local dev machine.
- Notes: For meaningful benchmarks, add a dedicated perf script + sample corpus.

## Follow-ups

- Consider adding a larger real-world HTML corpus and timing with `time` or `pytest-benchmark`.
- Capture diff reports when new golden cases are added.
