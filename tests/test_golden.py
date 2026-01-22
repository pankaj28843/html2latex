from __future__ import annotations

import json
from pathlib import Path

import pytest

from html2latex.html2latex import html2latex

CASES_DIR = Path(__file__).parent / "golden"


def _load_cases():
    cases = []
    for path in sorted(CASES_DIR.glob("*.json")):
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        for case in data:
            case["source"] = path.name
            cases.append(case)
    return cases


def _normalize(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    return "\n".join(line.rstrip() for line in stripped.splitlines())


@pytest.mark.parametrize(
    "case",
    _load_cases(),
    ids=lambda case: f"{case.get('source', 'cases.json')}::{case.get('name', 'case')}",
)
def test_golden_case(case):
    if case.get("skip"):
        pytest.skip(case["skip"])
    if case.get("xfail"):
        pytest.xfail(case["xfail"])

    result = html2latex(case["html"])
    assert _normalize(result) == _normalize(case["expected"])
