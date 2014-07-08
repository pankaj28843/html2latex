# -*- coding: utf-8 -*-
import os
import re
import sys

import htmlentitydefs
import jinja2
from lxml import etree


REGEX_TEXT_REPLACEMENTS = (
    # period
    (re.compile(r'([0-9]*)\s*(\.)(\s*)([0-9]*)?'), ignore_decimals_numbers),
    # comma
    (re.compile(r'([0-9]*)\s*(,)(\s*)([0-9]*)?'),
     ignore_comma_separated_numbers),
)


def ignore_decimals_numbers(match):
    groups = list(match.groups())
    groups[0] = groups[0].rstrip()
    groups[3] = groups[3].lstrip()

    if groups[0] and not groups[3]:
        return u"{0}. ".format(groups[0])
    elif groups[3] and not groups[0]:
        return u". {0}".format(groups[3])
    elif groups[0] and groups[3]:
        return u"".join(groups)
    else:
        return ". "


def ignore_comma_separated_numbers(match):
    groups = list(match.groups())
    groups[0] = groups[0]
    groups[3] = groups[3]

    if groups[0] and not groups[3]:
        return u"{0}, ".format(groups[0])
    elif groups[3] and not groups[0]:
        return u", {0}".format(groups[3])
    elif groups[0] and groups[3]:
        return u"".join(groups)
    else:
        return ", "


def fix_text(s):
    for pattern, replacement in REGEX_TEXT_REPLACEMENTS:
        s = pattern.sub(replacement, s)
    return s

REGEX_FORMATTING_REPLACEMENTS = (
    # colon
    (re.compile(r'\s*:\s*'), r': '),
    # semi colon
    (re.compile(r'\s*;\s*'), r'; '),
    # question mark
    (re.compile(r'\s*\?\s*'), r'? '),
    # parenthesis
    (re.compile(r'\s*\(\s*([^\)]*)\s*\)\s*'), r' (\1) '),
    # remove \par from end
    (re.compile(r'\\par\s*$'), r''),
    (re.compile(r'>'), r'\\textgreater '),
    (re.compile(r'&gt;'), r'\\textgreater '),
    (re.compile(r'<'), r'\\textless '),
    (re.compile(r'&lt;'), r'\\textless '),
)

REGEX_COMPLEX_FORMATTING_REPLACEMENTS = (
    """
    Quoted text using single or double quotes
    """
    (re.compile(
        r'\s*"\s*([^"]*)\s*([.?]{0,1})\s*"\s*([.?]{0,1})\s*'), r' ``{0}{1}{2}" '),
    (re.compile(
        r'\s*\'\s*([^\']*)\s*([.?]{0,1})\s*\'\s*([.?]{0,1})\s*'), r" `{0}'{1}{2} "),
    # quoted text using apostrophe etc.
    (re.compile(
        r'“\s*([^”]*)\s*([.?]{0,1})\s*”\s*([.?]{0,1})\s*'), r' ``{0}{1}{2}" '),
    (re.compile(
        r'\s*‘\s*([^’]*)\s*([.?]{0,1})\s*’\s*([.?]{0,1})\s*'), r" `{0}'{1}{2} "),
)


def fix_formatting(s):
    for pattern, replacement in REGEX_FORMATTING_REPLACEMENTS:
        s = pattern.sub(replacement, s)

    if s.startswith("A)"):
        s = "a)" + s[2:]

    if s.startswith("\\noindent A)"):
        s = "\\noindent a)" + s[12:]

    for pattern, replacement in REGEX_COMPLEX_FORMATTING_REPLACEMENTS:
        def fixup(match):
            stripped_groups = [g.rstrip() for g in match.groups()]
            stripped_groups[0] = fix_formatting(stripped_groups[0])
            return replacement.format(*stripped_groups)
        s = pattern.sub(fixup, s)

    pattern = re.compile(
        r'(?:\\includegraphics\s*\[\s*[^\]]*\s*\]\s*\{\s*[^\}]*\s*\}\s*|\\scalegraphics\s*\{\s*[^\}]*\s*\}\s*)+')
    for graphic in re.findall(pattern, s):
        # s = s.replace(
        #     graphic, "\\begin{center}" + graphic.strip() + "\end{center}")
        # s = s.replace(graphic, "IMAGEWILDCARD" + graphic.strip())
        s = s.replace(graphic, graphic.strip())

    return s


PRARAGRAPH_ENDING_CLEANERS = (
    (re.compile(r"(?:&nbsp;\s*)+</p>"), "</p>"),
    (re.compile(r"(?:<br\s*/>\s*)+</p>"), "</p>"),
    (re.compile(r"(?:<br\s*>\s*)+</p>"), "</p>"),
    (re.compile(r"\s*</p>"), "</p>"),
    # (re.compile(r"<p>\s*</p>"), ""),
)


def clean_paragraph_ending(html):
    for pattern, replacement in PRARAGRAPH_ENDING_CLEANERS:
        html = pattern.sub(replacement, html)

    html = re.sub(r"\s*/>", "/>", html.rstrip())
    root = etree.HTML(html)
    for element in root.iterdescendants():
        if element.tag == "u":
            _html = etree.tostring(element)
            html = html.replace(_html, re.sub(r"<br\s*/>", " ", _html))
    return html
