# -*- coding: utf-8 -*-

# Standard Library
import hashlib
import htmlentitydefs
import re

# Third Party Stuff
import redis
from lxml import etree

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

REGEX_LATEX_SUBS = (
    (re.compile(r'\\'), r'\\textbackslash '),
    (re.compile(r'>'), r"\\textgreater "),
    (re.compile(r'&gt;'), r"\\textgreater "),
    (re.compile(r'<'), r'\\textless '),
    (re.compile(r'&lt;'), r'\\textless '),
    (re.compile(r'&degree;'), r'\\degree '),
    (re.compile(r'([{}_#%&$])'), r'\\\1'),
    (re.compile(r'~'), r'\~'),
    (re.compile(r'-'), r'\\textendash '),
    (re.compile(r'\^'), r'\^'),
    (re.compile(r'"'), r"''"),
    (re.compile(r'\.\.\.+'), r'\\ldots '),
)

REGEX_UNESCAPE_LATEX_SUBS = (
    # (re.compile(r'\\textbackslash '), r'\\'),
    # (re.compile(r'\\textgreater '), r'>'),
    # (re.compile(r'\\textgreater '), r'&gt;'),
    # (re.compile(r'\\textgreater '), r'>'),
    # (re.compile(r'\\textless '), r'&lt;'),
    # (re.compile(r'\\degree '), r'&degree;'),


    # (re.compile(r'\\([\[{}_#%&$\]])'), r'(\1)'),
    # (re.compile(r'\~{}'), r'~'),
    # (re.compile(r'\\textendash '), r'-'),
    # (re.compile(r'\^{}'), r'\^'),
    # (re.compile(r'"'), r"''"),
    (re.compile(r'\\ldots '), r'....'),
    (re.compile(r"''"), r'"'),
    (re.compile(r'\^'), r'^'),
    (re.compile(r'\\~'), r'~'),
    (re.compile(r'\['), '\lbrack '),
    (re.compile(r'\]'), '\\rbrack '),
    (re.compile(r'\\([{}_#%&$])'), r'\1'),
    (re.compile(r'\\degree '), r'&degree;'),
    #(re.compile(r'\\textless '), r'&lt;'),
    (re.compile(r'\\textgreater '), r'>'),
    #(re.compile(r'\\textgreater '), r'&gt;'),
    (re.compile(r'\\textless '), r'<'),
    (re.compile(r'\\textbackslash '), r'\\'),
)
#     (re.compile(r'\\textgreater '), r'>'),
#     (re.compile(r'\\textgreater '), r'&gt;'),
#     (re.compile(r'\\textless '), r'<'),
#     (re.compile(r'\\textless '), r'&lt;'),
#     (re.compile(r'\\degree '), r'&degree;'),


def latex_for_html(html):
    hashed_html = u"webkit2png-{0}".format(hashlib.sha512(html).hexdigest())
    return redis_client.get(hashed_html)


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
    # if "The nature of the roots of the quadratic equation" in text:
    #     import ipdb; ipdb.set_trace()

    '''Escape some latex special characters'''
    text = text.replace('[', '\lbrack ')
    text = text.replace(']', '\\rbrack ')

    text = re.sub(
        r'([{}$])',
        r'\\\1',
        re.sub(
            r'\\([{}$])',
            r'\1',
            text
        )
    )

    items = (
        (r'&', r'\&'),
        (r'#', r'\#'),
        (r'_', r'\underline{\thickspace}'),
        (r'-', r'\textendash\,'),
        (r'%', r'\%'),
        (r'\\%', r'\%'),
        (r'\rm', r'\mathrm'),
    )
    for oldvalue, newvalue in items:
        text = text.replace(oldvalue, newvalue)

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
        (u'â', '\''),
        (u'â', ''),
        #(u'â', '``'),
        #(u'â', '\'\''),
    )
    for oldvalue, newvalue in items:
        text = text.replace(oldvalue, newvalue)

    return text


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
    # (re.compile(r'>'), r'\\textgreater '),
    # (re.compile(r'&gt;'), r'\\textgreater '),
    # (re.compile(r'<'), r'\\textless '),
    # (re.compile(r'&lt;'), r'\\textless '),
)


REGEX_COMPLEX_FORMATTING_REPLACEMENTS = (
    # Quoted text using single or double quotes
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

REGEX_CLEAN_PRARAGRAPH_ENDING = r'|'.join((
    r"(?:&nbsp;\s*)+</p>",
    r"(?:<br\s*/>\s*)+</p>",
    r"(?:<br\s*>\s*)+</p>",
    r"\s+</p>",))

REGEX_PRARAGRAPH_ENDING_CLEANERS = (
    # Following patterns are commented out because we don't want to do anything
    # with intended empty p tags. Empty p tags can be created by pressing Enter
    # key in CKEditor

    # Next 4 patterns are to remove empty paragraphs
    # (re.compile(r"<p>\s*(?:\s*&nbsp;\s*)+\s*</p>"), ""),
    # (re.compile(r"<p>\s*(?:\s*<br\s*/>\s*)+\s*</p>"), ""),
    # (re.compile(r"<p>\s*(?:\s*<br\s*>\s*)+\s*</p>"), ""),
    # (re.compile(r"<p>\s*</p>"), ""),

    # Remove empty tags from the last paragraph
    (re.compile(REGEX_CLEAN_PRARAGRAPH_ENDING), "</p>"),
)


def ignore_decimals_numbers(match):
    """
    Returns string with space after dot
    """
    groups = list(match.groups())
    groups[0] = groups[0]
    groups[3] = groups[3]

    if groups[0] and not groups[3]:
        return u"{0}. ".format(groups[0])
    elif groups[3] and not groups[0]:
        return u". {0}".format(groups[3])
    elif groups[0] and groups[3]:
        return u"".join(groups)
    else:
        return ". "


def ignore_comma_separated_numbers(match):
    """
    Returns string with space after comma
    """
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


REGEX_TEXT_REPLACEMENTS = (
    # period
    (re.compile(r'([0-9]*)\s*(\.)(\s*)([0-9]*)?'), ignore_decimals_numbers),
    # comma
    (re.compile(r'([0-9]*)\s*(,)(\s*)([0-9]*)?'),
     ignore_comma_separated_numbers),
)


def fix_text(text):
    for pattern, replacement in REGEX_TEXT_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    return text


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


def clean_paragraph_ending(html):
    """
    Fixes paragraph to exclude extra spaces and extra lines
    """

    html = re.sub(r"\s*/>", "/>", html.rstrip())
    root = etree.HTML(html)
    body = root.find(".//body")

    if (list(root.iterdescendants())[0].tag == "p" or
            body.getchildren()[-1].tag != "p"):
        """
        Don't clean if outermost tag is not a paragraph tag or if p is not the
        last descendant.
        """
        return html

    for pattern, replacement in REGEX_PRARAGRAPH_ENDING_CLEANERS:
        # Clean in a loop till a pattern is matched!
        while pattern.search(html):
            html = pattern.sub(replacement, html)

    for element in root.iterdescendants():
        if element.tag == "u":
            _html = etree.tostring(element)
            html = html.replace(_html, re.sub(r"<br\s*/>", " ", _html))
    return html
