from pathlib import Path

from html2latex.utils.test_summary import build_test_summary_lines


def test_golden_summary_matches_baseline() -> None:
    baseline = Path("tests/golden/test-summary.txt")
    assert baseline.exists(), (
        "Missing tests/golden/test-summary.txt; run scripts/update_test_summary.py"
    )
    expected = baseline.read_text(encoding="utf-8").splitlines()
    assert build_test_summary_lines(Path("tests/golden")) == expected
