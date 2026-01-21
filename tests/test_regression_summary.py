import json
from pathlib import Path


def _current_summary_lines() -> list[str]:
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
    return lines


def test_golden_summary_matches_baseline() -> None:
    baseline = Path("tests/golden/test-summary.txt")
    assert baseline.exists(), (
        "Missing tests/golden/test-summary.txt; run scripts/update_test_summary.py"
    )
    expected = baseline.read_text(encoding="utf-8").splitlines()
    assert _current_summary_lines() == expected
