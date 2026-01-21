#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    golden_dir = Path("tests/golden")
    lines = []
    total = 0
    for path in sorted(golden_dir.glob("*.json")):
        cases = json.loads(path.read_text(encoding="utf-8"))
        for case in cases:
            name = case.get("name", "case")
            lines.append(f"{path.name}: {name}")
            total += 1
    lines.append("")
    lines.append(f"TOTAL: {total}")
    (golden_dir / "test-summary.txt").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
