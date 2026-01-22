from __future__ import annotations

import json
from pathlib import Path


def build_test_summary_lines(golden_dir: Path) -> list[str]:
    lines: list[str] = []
    total = 0
    for path in sorted(golden_dir.glob("*.json")):
        cases = json.loads(path.read_text(encoding="utf-8"))
        for case in cases:
            name = case.get("name", "case")
            lines.append(f"{path.name}: {name}")
            total += 1
    lines.append("")
    lines.append(f"TOTAL: {total}")
    return lines
