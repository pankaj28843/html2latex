"""Centralized HTML tag classification for the html2latex pipeline.

This module provides a single source of truth for HTML tag categorization,
ensuring consistency between the normalization and conversion pipeline stages.

When adding or removing tags from these sets, update all relevant documentation
and tests to maintain consistency.
"""

from __future__ import annotations

__all__ = [
    "BLOCK_PASSTHROUGH",
    "BLOCK_TAGS",
    "INLINE_PASSTHROUGH",
]

# Block-level elements that affect whitespace normalization and LaTeX structure.
# These tags are treated as block containers in the normalization pipeline.
BLOCK_TAGS: frozenset[str] = frozenset(
    {
        "article",
        "aside",
        "blockquote",
        "body",
        "caption",
        "dd",
        "div",
        "dl",
        "dt",
        "figure",
        "figcaption",
        "footer",
        "header",
        "html",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "tbody",
        "td",
        "tfoot",
        "th",
        "thead",
        "tr",
        "ul",
    }
)

# Block elements that pass through to their children without
# generating LaTeX structure (semantic HTML5 containers).
BLOCK_PASSTHROUGH: frozenset[str] = frozenset(
    {
        "article",
        "aside",
        "footer",
        "header",
        "main",
        "nav",
        "section",
    }
)

# Inline elements that pass through to their children without
# generating LaTeX commands (semantic inline containers).
INLINE_PASSTHROUGH: frozenset[str] = frozenset(
    {
        "abbr",
        "dfn",
        "span",
        "time",
    }
)
