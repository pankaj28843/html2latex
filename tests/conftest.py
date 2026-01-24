"""Pytest configuration and fixtures for html2latex tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.harness import load_fixture_cases


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options."""
    parser.addoption(
        "--fixture-filter",
        action="append",
        default=[],
        help="Only run html2latex fixtures with case_id prefixes (repeatable).",
    )


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """Parametrize tests with fixture cases."""
    if "fixture_case" not in metafunc.fixturenames:
        return
    filters = metafunc.config.getoption("--fixture-filter") or []
    cases = load_fixture_cases(filters=filters, include_errors=False)
    metafunc.parametrize("fixture_case", cases, ids=lambda case: case.case_id)


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Apply markers to tests based on their directory location."""
    for item in items:
        # Get the path relative to tests/
        test_path = Path(item.fspath)
        parts = test_path.parts

        # Apply markers based on directory
        if "unit" in parts:
            item.add_marker(pytest.mark.unit)
        elif "integration" in parts:
            item.add_marker(pytest.mark.integration)
        elif "e2e" in parts:
            item.add_marker(pytest.mark.e2e)
        elif "performance" in parts:
            item.add_marker(pytest.mark.slow)

        # Mark LaTeX validity tests as slow (requires LaTeX compilation)
        if "test_latex_validity" in test_path.name:
            item.add_marker(pytest.mark.slow)
            item.add_marker(pytest.mark.e2e)
