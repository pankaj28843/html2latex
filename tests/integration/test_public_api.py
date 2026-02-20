"""Test that documented public API imports work correctly.

These tests validate the import patterns shown in README.md to catch
documentation drift and ensure IDE/Pylance compatibility.
"""

import pytest


@pytest.mark.integration
class TestPublicAPIImports:
    """Verify all documented import patterns work."""

    def test_top_level_html2latex_import(self):
        """Test: from html2latex import html2latex."""
        from html2latex import html2latex

        result = html2latex("<p>Hello World</p>")
        assert "Hello World" in result
        assert "\\par" in result

    def test_top_level_render_import(self):
        """Test: from html2latex import render."""
        from html2latex import render

        result = render("<p>Test</p>")
        assert "\\documentclass" in result
        assert "Test" in result

    def test_top_level_converter_import(self):
        """Test: from html2latex import Converter, ConvertOptions."""
        from html2latex import Converter, ConvertOptions

        converter = Converter(ConvertOptions(strict=False))
        result = converter.convert("<a href='https://example.com'>Link</a>")

        assert "Link" in result.body
        assert "hyperref" in result.packages

    def test_top_level_latex_document_import(self):
        """Test: from html2latex import LatexDocument."""
        from html2latex import LatexDocument

        assert LatexDocument is not None

    def test_all_exports_accessible(self):
        """Verify __all__ exports are accessible from top-level."""
        import html2latex

        expected_exports = [
            "ConvertOptions",
            "Converter",
            "LatexDocument",
            "convert",
            "html2latex",
            "render",
        ]

        for export in expected_exports:
            assert hasattr(html2latex, export), f"Missing export: {export}"
