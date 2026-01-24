"""Jinja2 template rendering for LaTeX documents."""

from __future__ import annotations

from jinja2 import Environment

__all__ = [
    "build_environment",
    "render_document",
]

_DEFAULT_TEMPLATE = """\\documentclass{article}
{{ preamble }}
\\begin{document}
{{ body }}
\\end{document}
"""


def build_environment() -> Environment:
    """Build a Jinja2 environment configured for LaTeX output.

    Note: autoescape=False is intentional - we're generating LaTeX, not HTML.
    LaTeX special characters are escaped during conversion, not by Jinja2.
    """
    return Environment(
        autoescape=False,  # noqa: S701
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )


def render_document(
    body: str,
    *,
    preamble: str = "",
    template: str | None = None,
) -> str:
    """Render a LaTeX document using a Jinja2 template.

    Args:
        body: The LaTeX body content.
        preamble: Optional LaTeX preamble content.
        template: Optional custom Jinja2 template string.

    Returns:
        The rendered LaTeX document as a string.
    """
    env = build_environment()
    tmpl = env.from_string(template or _DEFAULT_TEMPLATE)
    return tmpl.render(body=body, preamble=preamble)
