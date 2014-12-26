# -*- coding: utf-8 -*-
# Standard Library
import hashlib
import htmlentitydefs
import os
import re
import subprocess
import sys
import uuid

# Third Party Stuff
import enchant
import jinja2
import redis
from html2text import html2text
from lxml import etree
from PIL import Image
from splinter import Browser

from .webkit2png import webkit2png

redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
browser = Browser('phantomjs')


def get_image_size(path):
    img = Image.open(path)
    return img.size


def latex_for_html(html):
    hashed_html = u"webkit2png-{0}".format(hashlib.sha512(html).hexdigest())
    return redis_client.get(hashed_html)


def get_image_for_html_table(html, do_spellcheck=False):
    html = html.strip()
    if do_spellcheck:
        html = check_spelling_in_html(html)

    wait_time = 0
    root = etree.HTML(html)
    if root.find('.//span[@class="math-tex"]') is not None:
        # mathjax equations present
        wait_time = 5

    REGEX_SN = re.compile(r'(?i)\s*(s\s*\.*\s*no\.*|s\s*\.*\s*n\.*)\s*')
    td = root.find(".//td")
    if td is not None and td.find('.//span[@class="math-tex"]') is None:
        td_html = etree.tostring(td)
        html = html.replace(td_html, REGEX_SN.sub(" SN ", td_html, 1), 1)

    hashed_html = u"webkit2png-{0}".format(hashlib.sha512(html).hexdigest())

    existing_image_file = redis_client.get(hashed_html)

    if existing_image_file:
        if os.path.isfile(existing_image_file):
            return existing_image_file

    context = {
        "table_inner_html": html,
        "STATIC_ROOT": settings.STATIC_ROOT,
        "MATHAJAX_ROOT": settings.MATHAJAX_ROOT,
    }
    html = render_to_string(
        'web2png-table.html', context)
    unique_id = str(uuid.uuid4())
    html_file = u"/var/tmp/{0}.html".format(unique_id)
    with open(html_file, "wb") as f:
        f.write(html)
    image_file = u"/var/tmp/{0}.png".format(unique_id)
    url = u"file://{0}".format(html_file)
    if wait_time > 0:
        webkit2png(url, image_file, browser=browser, wait_time=wait_time)
    else:
        p = subprocess.Popen(
            ["webkit2png.py", "-o", image_file, html_file])
        p.wait()

    redis_client.set(hashed_html, image_file)

    return image_file

enchant_dictionary = enchant.Dict("en_UK")
invalid_word_checker = lambda w: not enchant_dictionary.check(w)


def check_spelling(text):
    incorrect_words = filter(
        invalid_word_checker, set(re.findall("[a-zA-Z]+", text)))
    for word in incorrect_words:
        text = text.replace(
            word, r"\textcolor{red}{\Large \textbf{" + word + "}}")
    return text


def check_spelling_in_html(html):
    incorrect_words = filter(
        invalid_word_checker, set(re.findall("[a-zA-Z]+", html2text(html))))
    for word in incorrect_words:
        html = html.replace(
            word, r'<strong style="color: red; font-size: 14px;">' + word + '</strong>')
    return html


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

# Functions for outputting message to stderr


def warning_message(message, newLine=True):
    '''Output a warning message to stderr.'''
    sys.stderr.write('WARNING: ' + message)
    if newLine:
        sys.stderr.write('\n')


def information_message(message, newLine=True):
    '''Output an information message to stderr.'''
    sys.stderr.write('INFO: ' + message)
    if newLine:
        sys.stderr.write('\n')


def error_message(message, newLine=True, terminate=True):
    global commandlineArguments
    sys.stderr.write('ERROR: ' + message)
    if newLine:
        sys.stderr.write('\n')
    if terminate:
        sys.exit()


# Some boilerplate to use jinja more elegantly with LaTeX
# http://flask.pocoo.org/snippets/55/

LATEX_SUBS = (
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


def escape_tex(value):
    newval = value
    for pattern, replacement in LATEX_SUBS:
        newval = pattern.sub(replacement, newval)
    return newval

#
# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.


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
    text = text.replace(r'&', r'\&')
    text = text.replace(r'#', r'\#')
    text = text.replace(r'_', r'\underline{\thickspace}')
    text = text.replace(r'%', r'\%')
    text = text.replace(r'\\%', r'\%')
    text = text.replace(r'\\%', r'\%')
    # fix some stuff
    text = text.replace(r'\rm', r'\mathrm')
    return text


UNESCAPE_LATEX_SUBS = (
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


def unescape_latex(text):
    text = text.replace(r'\%', r'%')
    text = text.replace(r'\underline{\thickspace}', r'_')
    text = text.replace(r'\_', r'_')
    text = text.replace(r'\#', r'#')
    text = text.replace(r'\&', r'&')

    for pattern, replacement in UNESCAPE_LATEX_SUBS:
        text = pattern.sub(replacement, text)

    return text


def clean(text):
    text = text.replace(u'Â', ' ')
    text = text.replace(u'â', '')
    text = text.replace(u'â', '')
    text = text.replace(u'''
''', '\n')
    text = text.replace(u'â', '\'')
    text = text.replace(u'â', '')
    text = text.replace(u'â', '``')
    text = text.replace(u'â ', '\'\'')
    text = text.replace(u'\u00a0', ' ')
    text = text.replace(u'\u00c2', ' ')
    return text


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


REGEX_TEXT_REPLACEMENTS = (
    # period
    (re.compile(r'([0-9]*)\s*(\.)(\s*)([0-9]*)?'), ignore_decimals_numbers),
    # comma
    (re.compile(r'([0-9]*)\s*(,)(\s*)([0-9]*)?'),
     ignore_comma_separated_numbers),
)


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
