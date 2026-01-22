#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from html2latex.utils.test_summary import build_test_summary_lines


def main() -> None:
    golden_dir = Path("tests/golden")
    lines = build_test_summary_lines(golden_dir)
    (golden_dir / "test-summary.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
