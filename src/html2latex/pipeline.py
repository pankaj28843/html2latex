# -*- coding: utf-8 -*-
"""Pipeline entry points for HTML to LaTeX conversion."""

from __future__ import annotations

import re

from .elements import delegate
from .html_adapter import parse_html
from .utils.html import check_if_html_has_text
from .utils.text import escape_latex

_RE_E_G = re.compile(r"(?i)e\. g\.")
_RE_I_E = re.compile(r"(?i)i\. e\.")
_RE_UNDERSCORES = re.compile(r"s+_+|\s*_{2,}")
_RE_TEXTSUP = re.compile(
    r"([a-zA-Z0-9]+)\s*\\begin\{textsupscript\}\s*(\w+)\s*\\end\{textsupscript\}"
)
_RE_TEXTSUB = re.compile(
    r"([a-zA-Z0-9]+)\s*\\begin\{textsubscript\}\s*(\w+)\s*\\end\{textsubscript\}"
)
_RE_NOINDENT_PAR = re.compile(r"\\noindent\s*\\par")


def fix_encoding_of_html_using_lxml(html: str) -> str:
    # Legacy name retained for compatibility; uses justhtml now.
    fixed_html = parse_html(html).root.to_html()

    if re.search(r"^<p>", html) is None:
        fixed_html = re.sub(r"^<p>", "", fixed_html)
    if re.search(r"</p>$", html) is None:
        fixed_html = re.sub(r"</p>$", "", fixed_html)

    return fixed_html


def html2latex(html: str, **kwargs):
    html = html.strip()
    if not html:
        return ""

    html = fix_encoding_of_html_using_lxml(html)
    return _html2latex(html, **kwargs)


def _html2latex(html: str, do_spellcheck: bool = False, **kwargs):
    """
    Converts Html Element into LaTeX
    """
    # If html string has no text then don't need to do anything
    if not check_if_html_has_text(html):
        return ""

    parsed = parse_html(html)
    body = parsed.root.find(".//body")
    if body is None:
        body = parsed.root

    line_separator = kwargs.get("LINE_SPERATOR", "")

    content = line_separator.join(
        [delegate(element, do_spellcheck=do_spellcheck, **kwargs) for element in body]
    )

    output = content

    output = _RE_E_G.sub("e.g.", output)
    output = _RE_I_E.sub("i.e.", output)

    for underscore in _RE_UNDERSCORES.findall(output):
        output = output.replace(underscore, escape_latex(underscore), 1)

    output = _RE_TEXTSUP.sub(r"\\begin{math}\1^{\2}\\end{math}", output)
    output = _RE_TEXTSUB.sub(r"\\begin{math}\1_{\2}\\end{math}", output)

    if isinstance(output, bytes):
        output = output.decode("utf-8")

    items = (
        ("\u009f", ""),
        ("\u2715", "\u00d7"),
        ("\u2613", "\u00d7"),
        ("\u0086", "\u00b6"),
        ("\u2012", "-"),
        ("\u25b3", "\u2206"),
        ("||", "\\begin{math}\\parallel\\end{math}"),
        ("\u03f5", "\\epsilon "),
    )
    for oldvalue, newvalue in items:
        output = output.replace(oldvalue, newvalue)

    output = output.replace("begin{bfseries}", "begin{bfseries} ")
    output = output.replace("\\end{bfseries}", " \\end{bfseries} ")
    output = output.replace("begin{underline}", "begin{underline} ")
    output = output.replace("\\end{underline}", " \\end{underline} ")

    output = _RE_NOINDENT_PAR.sub(r"\\vspace{11pt}", output)

    output = output.replace(r"\end{math}\\textendash", r"\end{math}\textendash")

    output = output.replace(r"\end{math}\\\textendash", r"\end{math}\textendash")

    output = output.replace(r"\end{math}\\\\textendash", r"\end{math}\textendash")

    output = output.replace(r"\end{math}\+", r"+ \end{math}")

    output = output.replace(r"\end{math}\\+", r"+ \end{math}")

    output = output.replace(r"\end{math}\\\+", r"+ \end{math}")

    output = output.replace(r"\end{math}\\\\+", r"+ \end{math}")

    output = output.replace(r"\end{math}\\-", r"- \end{math}")

    output = output.replace(r"\end{math}\\\-", r"- \end{math}")

    output = output.replace(r"\end{math}\\\\-", r"- \end{math}")

    if r"\end{math}\\" in output:
        raise Exception

    return output
