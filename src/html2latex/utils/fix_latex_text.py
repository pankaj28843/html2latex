# -*- coding: utf-8 -*-

import hashlib
import os
import re
import redis
import htmlentitydefs
import jinja2


from .webkit2png import webkit2png

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

REGEX_LATEX_SUBS = (
    (re.compile(r'\\'), r'\\textbackslash '),
    (re.compile(r'([{}_#%&$])'), r'\\\1'),
    (re.compile(r'~'), r'\~{}'),
    # (re.compile(r'-'), r'\\textendash '),
    (re.compile(r'\^'), r'\^{}'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\.\.\.+'), r'\\ldots '),
    (re.compile(r'>'), r'\\textgreater '),
    (re.compile(r'&gt;'), r'\\textgreater '),
    (re.compile(r'<'), r'\\textless '),
    (re.compile(r'&lt;'), r'\\textless '),
    (re.compile(r'&degree;'), r'\\degree '),
    # (re.compile(r''), r''),
    # (re.compile(r''), r''),
    # (re.compile(r''), r''),
)

REGEX_UNESCAPE_LATEX_SUBS = (
    (re.compile(r'\\textbackslash '), r'\\'),
    (re.compile(r'\\([\[{}_#%&$\]])'), r'(\1)'),
    (re.compile(r'\~{}'), r'~'),
    # (re.compile(r'\\textendash '), r'-'),
    (re.compile(r'\^{}'), r'\^'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\\ldots '), r'\.\.\.+'),
    (re.compile(r'\\textgreater '), r'>'),
    (re.compile(r'\\textgreater '), r'&gt;'),
    (re.compile(r'\\textless '), r'<'),
    (re.compile(r'\\textless '), r'&lt;'),
    (re.compile(r'\\degree '), r'&degree;'),
)


def latex_for_html(html):
    hashed_html = u"webkit2png-{0}".format(hashlib.sha512(html).hexdigest())
    return redis_client.get(hashed_html)


def setup_texenv(loader):
    texenv = jinja2.Environment(loader=loader)
    texenv.block_start_string = '((*'
    texenv.block_end_string = '*))'
    texenv.variable_start_string = '((('
    texenv.variable_end_string = ')))'
    texenv.comment_start_string = '((='
    texenv.comment_end_string = '=))'
    texenv.filters['escape_tex'] = escape_tex

    return texenv


"""
   Some boilerplate to use jinja more elegantly with LaTeX
   http://flask.pocoo.org/snippets/55/
"""


def escape_tex(value):
    newval = value
    for pattern, replacement in REGEX_LATEX_SUBS:
        newval = pattern.sub(replacement, newval)
    return newval


"""
 Removes HTML or XML character references and entities from a text string.

 @param text The HTML (or XML) source text.
 @return The plain text, as a Unicode string, if necessary.
"""


def unescape(text):
    text = text.replace("&nbsp;", "\\hspace{1pt}")

    def fixup(m):
        text = m.group(0)
        if text[:2] == "&#":
            # character reference
            try:
                if text[:3] == "&#x":
                    return unichr(int(text[3:-1], 16))
                else:
                    return unichr(int(text[2:-1]))
            except ValueError:
                pass
        else:
            # named entity
            try:
                text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
            except KeyError:
                pass
        return text  # leave as is
    return re.sub("&#?\w+;", fixup, text)


def escape_latex(text):
    '''Escape some latex special characters'''
    items = (
        (r'&', r'\&'),
        (r'#', r'\#'),
        (r'_', r'\underline{\thickspace}'),
        (r'%', r'\%'),
        (r'\\%', r'\%'),
        (r'\rm', r'\mathrm'),

    )
    for oldvalue, newvalue in items:
        ext = text.replace(oldvalue, newvalue)
    return text


def unescape_latex(text):
    """
    Return the string obtained by replacing the leftmost non-overlapping occurrences of pattern in string.
    """
    items = (
        (r'\%', r'%'),
        (r'\underline{\thickspace}', r'_'),
        (r'\_', r'_'),
        (r'\#', r'#'),
        (r'\&', r'&'),
    )
    for oldvalue, newvalue in items:
        text = text.replace(oldvalue, newvalue)

    for pattern, replacement in REGEX_UNESCAPE_LATEX_SUBS:
        text = pattern.sub(replacement, text)

    return text


def clean(text):
    """
    Replaces non-supported charcters into LaTeX characters.
    """
    items = (
        (u'Â', ' '),
        (u'â', ''),
        (u'â', ''),
        (u'''''', '\n'),
        (u'â', '\''),
        (u'â', ''),
        (u'â', '``'),
        (u'â ', '\'\''),
        (u'\u00a0', ' '),
        (u'\u00c2', ' '),
    )
    for oldvalue, newvalue in items:
        text = text.replace(oldvalue, newvalue)

    return text
