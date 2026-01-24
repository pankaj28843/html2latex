"""Integration tests for the Flask demo application.

These tests verify the demo app's API endpoints work correctly
without requiring a running Redis instance.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from flask.testing import FlaskClient

# Skip all tests in this module if Flask is not installed
flask = pytest.importorskip("flask")


class TestIndexRoute:
    """Tests for the GET / endpoint."""

    def test_index_returns_200(self, demo_client: FlaskClient) -> None:
        """GET / should return 200 OK."""
        response = demo_client.get("/")
        assert response.status_code == 200

    def test_index_returns_html(self, demo_client: FlaskClient) -> None:
        """GET / should return HTML content."""
        response = demo_client.get("/")
        assert b"<!DOCTYPE html>" in response.data or b"<html" in response.data


class TestConvertRoute:
    """Tests for the POST /convert endpoint."""

    def test_convert_valid_html_returns_latex(self, demo_client: FlaskClient) -> None:
        """POST /convert with valid HTML should return LaTeX."""
        response = demo_client.post(
            "/convert",
            data=json.dumps({"html_string": "<p>Hello World</p>"}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "latex" in data
        assert "Hello World" in data["latex"]

    def test_convert_empty_html_returns_latex(self, demo_client: FlaskClient) -> None:
        """POST /convert with empty HTML should return empty LaTeX."""
        response = demo_client.post(
            "/convert",
            data=json.dumps({"html_string": ""}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "latex" in data

    def test_convert_complex_html_returns_latex(self, demo_client: FlaskClient) -> None:
        """POST /convert with complex HTML should return proper LaTeX."""
        html = "<h1>Title</h1><p>Paragraph with <strong>bold</strong> text.</p>"
        response = demo_client.post(
            "/convert",
            data=json.dumps({"html_string": html}),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "latex" in data
        # Check for LaTeX constructs
        assert "Title" in data["latex"]
        assert "bold" in data["latex"]

    def test_convert_missing_html_string_returns_400(self, demo_client: FlaskClient) -> None:
        """POST /convert without html_string should return 400."""
        response = demo_client.post(
            "/convert",
            data=json.dumps({"wrong_field": "value"}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_convert_empty_body_returns_400(self, demo_client: FlaskClient) -> None:
        """POST /convert with empty body should return 400."""
        response = demo_client.post(
            "/convert",
            data="",
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_convert_invalid_json_returns_400(self, demo_client: FlaskClient) -> None:
        """POST /convert with invalid JSON should return 400."""
        response = demo_client.post(
            "/convert",
            data="not valid json",
            content_type="application/json",
        )
        assert response.status_code == 400


class TestErrorHandlers:
    """Tests for error handlers."""

    def test_404_returns_json(self, demo_client: FlaskClient) -> None:
        """404 errors should return JSON response."""
        response = demo_client.get("/nonexistent-route")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "Not found"
