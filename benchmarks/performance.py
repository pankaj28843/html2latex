#!/usr/bin/env python3
"""Simple performance benchmark for html2latex."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from time import perf_counter

from html2latex.html2latex import html2latex


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, math.ceil((pct / 100) * len(ordered)) - 1)
    return ordered[index]


def measure_html(html: str, repeats: int) -> list[float]:
    timings = []
    for _ in range(repeats):
        start = perf_counter()
        html2latex(html)
        timings.append((perf_counter() - start) * 1000)
    return timings


def load_cases(data_dir: Path) -> dict[str, str]:
    cases = {}
    for path in sorted(data_dir.glob("*.html")):
        cases[path.name] = path.read_text(encoding="utf-8")
    return cases


def load_baseline(path: Path | None) -> dict:
    if not path:
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=Path(__file__).parent / "data")
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--max-regression", type=float, default=0.2)
    args = parser.parse_args()

    cases = load_cases(args.data_dir)
    baseline = load_baseline(args.baseline)
    base_cases = baseline.get("cases", {})
    threshold = baseline.get("threshold_ratio")
    if threshold is None:
        threshold_percent = baseline.get("threshold_percent")
        if threshold_percent is not None:
            threshold = threshold_percent / 100 if threshold_percent > 1 else threshold_percent
    if threshold is None:
        threshold = args.max_regression

    regressions = []

    for name, html in cases.items():
        timings = measure_html(html, args.repeat)
        mean_ms = sum(timings) / len(timings)
        p95_ms = percentile(timings, 95)
        docs_per_sec = 1000 / mean_ms if mean_ms else 0.0

        record = {
            "case": name,
            "mean_ms": round(mean_ms, 3),
            "p95_ms": round(p95_ms, 3),
            "docs_per_sec": round(docs_per_sec, 2),
        }
        print(json.dumps(record))

        baseline_case = base_cases.get(name)
        if baseline_case:
            baseline_mean = float(baseline_case.get("mean_ms", 0))
            if baseline_mean and mean_ms > baseline_mean * (1 + threshold):
                regressions.append((name, mean_ms, baseline_mean))

    if regressions:
        print("Regression detected:")
        for name, mean_ms, baseline_mean in regressions:
            print(f"- {name}: {mean_ms:.3f}ms (baseline {baseline_mean:.3f}ms)")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
