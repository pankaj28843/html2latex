from __future__ import annotations

import json
from pathlib import Path

import pytest

from html2latex.html2latex import html2latex

CASES_PATH = Path(__file__).parent / "golden" / "cases.json"


def _load_cases():
    with CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize(value: str) -> str:
    stripped = value.strip()
    if not stripped:
        return ""
    return "\n".join(line.rstrip() for line in stripped.splitlines())


@pytest.mark.parametrize("case", _load_cases(), ids=lambda case: case.get("name", "case"))
def test_golden_case(case):
    if case.get("skip"):
        pytest.skip(case["skip"])
    if case.get("xfail"):
        pytest.xfail(case["xfail"])

    result = html2latex(case["html"])
    assert _normalize(result) == _normalize(case["expected"])
