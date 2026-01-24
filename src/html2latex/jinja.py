from __future__ import annotations

from jinja2 import Environment

_DEFAULT_TEMPLATE = """\\documentclass{article}
{{ preamble }}
\\begin{document}
{{ body }}
\\end{document}
"""


def build_environment() -> Environment:
    # NOTE: autoescape=False is intentional - we're generating LaTeX, not HTML.
    # LaTeX special characters are escaped during conversion, not by Jinja2.
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
    env = build_environment()
    tmpl = env.from_string(template or _DEFAULT_TEMPLATE)
    return tmpl.render(body=body, preamble=preamble)
