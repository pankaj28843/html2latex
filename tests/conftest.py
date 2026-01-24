"""Pytest configuration and fixtures for html2latex tests."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from tests.fixtures.harness import load_fixture_cases

if TYPE_CHECKING:
    from flask import Flask
    from flask.testing import FlaskClient


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


# Demo app fixtures - only available when Flask is installed
@pytest.fixture
def demo_app() -> Flask:
    """Create a test instance of the demo Flask application.

    This fixture adds the demo-app directory to sys.path temporarily
    to import the app module, then creates a test-configured app instance.
    """
    demo_app_path = Path(__file__).parent.parent / "demo-app"
    sys.path.insert(0, str(demo_app_path))
    try:
        # Import inside fixture to avoid import errors when Flask isn't available
        from app import create_app

        app = create_app(
            {
                "TESTING": True,
                "CACHE_ENABLED": False,  # Disable Redis caching for tests
            }
        )
        return app
    finally:
        sys.path.remove(str(demo_app_path))


@pytest.fixture
def demo_client(demo_app: Flask) -> FlaskClient:
    """Create a test client for the demo Flask application."""
    return demo_app.test_client()
