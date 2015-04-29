# -*- coding: utf-8 -*-
"""
Convert HTML generated from CKEditor to LaTeX environment.
"""
# Standard Library
import copy
import hashlib
import hmac
import os
import re
import subprocess

# Third Party Stuff
import jinja2
import lxml
import mmh3
import redis
from lxml import etree
from PIL import Image
from repoze.lru import lru_cache
from xamcheck_utils.html import check_if_html_has_text
from xamcheck_utils.text import unicodify

from .setup_texenv import setup_texenv
from .utils.html_table import get_image_for_html_table
from .utils.image import get_image_size
from .utils.spellchecker import check_spelling
from .utils.text import (
    clean,
    clean_paragraph_ending,
    escape_latex,
    escape_tex,
    fix_formatting,
    fix_text,
    unescape
)

capfirst = lambda x: x and x[0].upper() + x[1:]

loader = jinja2.FileSystemLoader(
    os.path.dirname(os.path.realpath(__file__)) + '/templates')
texenv = setup_texenv(loader)

VERSION = "0.0.23"
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
CAPFIRST_ENABLED = False
# Templates for each class here.


def delegate(element, do_spellcheck=False, **kwargs):
    """
    Takes html element in form of etree and converts it into string.
    """
    '''>>> from lxml import etree
       >>> root = etree.HTML('<h1>Title</h1>')
       >>> print delegate(root[0][0])
       \chapter{Title}'''
    # delegate the work to classes handling special cases

    # Filter out empty tags
    try:
        element.tag
    except AttributeError:
        pass

    if element.tag == 'div':
        my_element = HTMLElement(element, do_spellcheck, **kwargs)

    # elif element.tag == 'table':
    #     my_element = Table(element, do_spellcheck, **kwargs)
    elif element.tag == 'table':
        # my_element = Table(element, do_spellcheck, **kwargs)
        table_inner_html = u''.join([etree.tostring(e) for e in element])
        items = (
                ("&#13;", ""),
                ("&uuml;", "&#10003;"),
                ("&#252;", "&#10003;"),
                ("\\checkmark", "&#10003;"),
                (u"ü", "&#10003;"),

        )
        for oldvalue, newvalue in items:
            table_inner_html = table_inner_html.replace(oldvalue, newvalue)

        image_file = get_image_for_html_table(
            table_inner_html, do_spellcheck=do_spellcheck)

        new_html = u"<img src='{0}'/>".format(image_file)
        new_element = etree.HTML(new_html).find(".//img")
        my_element = IMG(new_element, is_table=True, **kwargs)
        my_element.content["is_table"] = True
    elif element.tag == 'tr':
        my_element = TR(element, do_spellcheck, **kwargs)
    elif element.tag == 'tdr':
        my_element = TD(element, do_spellcheck, **kwargs)
    elif element.tag == 'img':
        try:
            # import ipdb; ipdb.set_trace()
            my_element = IMG(element, do_spellcheck, **kwargs)
        except IOError:
            return ''
    elif element.tag == 'a':
        my_element = A(element, do_spellcheck, **kwargs)
    elif isinstance(element, etree._Comment):
        my_element = None  # skip XML comments
    else:
        # no special handling required
        my_element = HTMLElement(element, do_spellcheck, **kwargs)

    try:
        my_element
    except NameError:
        # error_message(u"Error with element!! %s\n\n" %
        #               etree.tostring(element), terminate=False)
        return ''

    if my_element is None:
        return ''
    else:
        return my_element.render()


class HTMLElement(object):

    def __init__(self, element, do_spellcheck=False, **kwargs):
        self.element = element
        self.do_spellcheck = do_spellcheck

        self._init_kwargs = copy.deepcopy(kwargs)
        for key, value in kwargs.iteritems():
            setattr(self, key, value)

        # we make a general dict to store the contents we send to the Jinja
        # templates.
        self.content = {}
        self.content[
            'text'] = self.element.text if self.element.text is not None else ''
        self.content[
            'tail'] = self.element.tail if self.element.tail is not None else ''
        self.content['tag'] = escape_latex(self.element.tag)

        """ Get attributes of the elements"""
        try:
            self.content['class'] = self.element.attrib['class']
        except KeyError:
            self.content['class'] = ''
        for a in self.element.attrib:
            self.content[a] = self.element.attrib[a]

        self.get_template()
        self.cap_first()
        self.fix_tail()
        self.spell_check()
        self.escape_latex_characters()

        def fix_spaces(self, match):
            group = match.groups()[0] or ""
            group = group.replace(" ", "\\,")
            return " " + group + " "

        self.content['text'] = re.sub(
            r'( )+?', ' ', self.content['text']).rstrip()

        self.render_children()

    def get_template(self):
        try:
            self.template = texenv.get_template(self.element.tag + '.tex')
        except jinja2.exceptions.TemplateNotFound:
            self.template = texenv.get_template('not_implemented.tex')
        except TypeError:
            # error_message(
            #     "Error in element: " + repr(self.element), terminate=False)
            self.template = texenv.get_template('error.tex')

    def cap_first(self):
        """Capitalize first alphabet of the element
        """
        return
        CAPFIRST_TAGS = ('li', 'p', 'td', 'th',)
        if self.element.tag in CAPFIRST_TAGS:
            self.content['text'] = capfirst(self.content['text'])

    def fix_tail(self):
        """Fix tail of the element to include spaces accordingly
        """
        tail = self.content['tail']
        if (len(tail) > 0) and (tail[0] in [' \t\r\n']):
            tail = ' ' + tail
        if (len(tail) > 0) and (tail[-1] in [' \t\r\n']):
            tail = tail + ' '
        self.content['tail'] = tail

    def spell_check(self):
        """Do spell check and highlight invalid words using enchant
        """
        if self.do_spellcheck:
            self.content['text'] = check_spelling(self.content['text'])
            self.content['tail'] = check_spelling(self.content['tail'])
        else:
            pass

    def escape_latex_characters(self):
        """escape latex characters from text
        """
        text = self.content['text']
        text = clean(text)
        text = escape_latex(text)
        text = fix_text(text)
        self.content['text'] = text.replace("\r", "\n")

        """escape latex characters from tail
        """
        tail = self.content['tail']
        tail = clean(tail)
        tail = escape_latex(tail)
        tail = fix_text(tail)
        self.content['tail'] = tail.replace("\r", "\n")

    # self.content['text'] = self.content['text'].replace(" ", "\\,")
    # self.content['text'] = re.sub(
    #     r' ( )* ?', fix_spaces, self.content['text'])
    # self.content['tail'] = self.content['tail'].replace(" ", "\\,")
    def render(self):
        # return an empty string if the content is empty
        # if self.content['text'].strip() == '' and self.content['tail'].strip() == '':
        #     return ''
        # else:
        return self.template.render(content=self.content)

    def render_children(self):
        if self.element.tag == "p":
            for child in self.element:
                if child.tag == "br":
                    self.content['text'] += "\\newline"
                    if child.tail:
                        self.content['text'] += child.tail
                else:
                    self.content['text'] += delegate(
                        child, do_spellcheck=self.do_spellcheck, **self._init_kwargs)
        else:
            for child in self.element:
                self.content['text'] += delegate(
                    child, do_spellcheck=self.do_spellcheck, **self._init_kwargs)

    def remove_empty(self):
        '''Must remove empty tags'''
        pass


class A(HTMLElement):

    """
    a href tag
    Gets the url stored in a href
    """

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        # make it a url if the 'href' attribute is set
        if 'href' in element.attrib.keys():
            self.content['url'] = element.attrib['href']
        else:
            self.content['url'] = self.content['text']


class Table(HTMLElement):

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        # check whether its html or cnxml table
        # html table
        # must get number of columns. # find maximum number of td elements
        # in a single row
        max_td = 0
        for row in element.findall('.//tr'):
            ncols = len(row.findall('.//td'))
            max_td = max([max_td, ncols])
            ncols = len(row.findall('.//th'))
            max_td = max([max_td, ncols])

        self.content['ncols'] = max_td
        ncols = max_td

        # try a fancy column specifier for longtable
        colspecifier = r"p{%1.3f\textwidth}" % (
            float(0.85 / ncols))
        # colspecifier = " c "
        self.content['cols'] = '|' + '|'.join(
            [colspecifier for i in range(int(ncols))]) + '|'
        patterns = [
            (re.compile(r'&\s+\\\\ \\hline', re.MULTILINE),
             r'\\tabularnewline \\hline'),
            (re.compile(r'\\tabularnewline \\hline\s+\\\\', re.MULTILINE),
             r'\\tabularnewline \\hline'),
        ]
        for pattern, replacement in patterns:
            self.content['text'] = pattern.sub(
                replacement, self.content['text'])

        self.content['text'] = self.content['text'].replace(
            '\\tabularnewline \\hline\n\\\\', '\\tabularnewline \\hline')

        # self.content['text'] = re.compile(r'&\s+\\\s+\hline', re.MULTILINE).sub(
        #     r'\tabularnewline \hline', self.content['text'])
        # self.content['text'] = self.content['text'].replace(
        #     r'& \\ \hline', r'\tabularnewline \hline')
        self.content['text'] = self.content['text'].replace('\\par', ' ')
        self.content['text'] = self.content['text'].replace('\n', '')
        self.content['text'] = self.content[
            'text'].replace('\\hline\n\\\\', '\\hline')

        self.template = texenv.get_template('table.tex')


class TR(HTMLElement):

    """
    Rows in html table
    """

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = texenv.get_template('tr.tex')


class TD(HTMLElement):

    """
    Columns in Html table
    """

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = texenv.get_template('td.tex')


class TH(HTMLElement):

    """
    Columns in Html table
    """

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = texenv.get_template('th.tex')


class IMG(HTMLElement):
    is_table = False

    def __init__(self, element, *args, **kwargs):
        # import ipdb; ipdb.set_trace()

        HTMLElement.__init__(self, element, *args, **kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.get_image_link()
        self.image_size()

    def get_image_link(self):
        """get the link to the image and download it."""
        self.src = self.element.attrib['src']

        # A Directory to store remote images.
        REMOTE_IMAGE_ROOT = '/var/tmp/html2latex-remote-images'
        GRAYSCALED_IMAGES = '/var/tmp/html2latex-grayscaled-images'

        # Make sure that directory exists.
        if not os.path.isdir(REMOTE_IMAGE_ROOT):
            os.makedirs(REMOTE_IMAGE_ROOT)

        # Make sure that directory exists.
        if not os.path.isdir(GRAYSCALED_IMAGES):
            os.makedirs(GRAYSCALED_IMAGES)

        # get the link to the image and download it.
        if self.src.startswith("http"):
            output_filename = re.sub(r"[^A-Za-z0-9\.]", "-", self.src)
            if len(output_filename) > 128:
                output_filename = hashlib.sha512(output_filename).hexdigest()
            output_filepath = os.path.normpath(os.path.join(REMOTE_IMAGE_ROOT, output_filename))

            if not os.path.splitext(output_filepath):
                output_filepath = output_filepath + ".png"

            if not os.path.isfile(output_filepath):
                p = subprocess.Popen(
                    ["wget", "-c", "-O", output_filepath, self.src], cwd=REMOTE_IMAGE_ROOT)
                p.wait()
                if not os.path.isfile(output_filepath):
                    raise Exception("Count not download the image file: {}.".format(self.src))

            self.src = self.element.attrib['src'] = output_filepath

        jpg_filename = ''.join(os.path.splitext(self.src)[:-1])
        jpg_filepath = os.path.normpath(os.path.join(
            GRAYSCALED_IMAGES,
            hashlib.sha512(jpg_filename).hexdigest() + '_grayscaled.jpg',
        ))

        if not os.path.isfile(jpg_filepath):
            p = subprocess.Popen(
                ["convert", self.src, '-type', 'Grayscale', jpg_filepath]
            )
            p.wait()

        self.src = self.element.attrib['src'] = jpg_filepath
        self.style = self.element.attrib.get('style', "")

    def image_size(self):
        """ Adjust image size according to requirements"""
        img_width = None
        img_height = None

        try:
            img_width = int(
                float(re.findall(r"width:(\d+)px", self.style)[0]) * 0.75)
        except IndexError:
            pass

        try:
            img_height = int(
                float(re.findall(r"height:(\d+)px", self.style)[0]) * 0.75)
        except IndexError:
            pass

        try:
            if img_width is None or img_height is None:
                width, height = get_image_size(self.src)
                img_width = 3. / 4 * width
                img_height = 3. / 4 * height
            if not self.is_table:
                image = Image.open(self.src)
                # new_image = image.convert("LA")
                # if image.size == new_image.size:
                #     image = new_image
                # enhancer = ImageEnhance.Brightness(image)
                # enhancer.enhance(1.1)
                # enhancer = ImageEnhance.Contrast(image)
                # enhancer.enhance(1.1)
                src = self.src + "grayscaled.png"
                image.save(src, quality=100)
        except IOError as e:
            raise e
            # width, height = (-1, -1)

        self.content['imagename'] = self.src
        self.content['imagewidth'], self.content[
            'imageheight'] = img_width, img_height

        self.template = texenv.get_template('img.tex')

    def render(self):
        try:
            ALIGN_IMAGE_IN_CENTER = self.ALIGN_IMAGE_IN_CENTER
        except AttributeError:
            ALIGN_IMAGE_IN_CENTER = False

        # import ipdb; ipdb.set_trace()
        context = {
            "content": self.content,
            "ALIGN_IMAGE_IN_CENTER": ALIGN_IMAGE_IN_CENTER,
        }
        output = self.template.render(**context)
        # import ipdb; ipdb.set_trace()
        # output = "\\begin{center}" + output + "\end{center}"
        return output


@lru_cache(512)
def hash_string(s):
    return "html2latex_{version}_{mmh3_hash}_{hmac_of_sha512_hash}".format(
        version=VERSION,
        mmh3_hash=mmh3.hash128(s),
        hmac_of_sha512_hash=hmac.new(hashlib.sha512(s).hexdigest()).hexdigest(),
    )


def fix_encoding_of_html_using_lxml(html_str):
    if html_str.startswith("<p>"):
        escaped_str = etree.tostring(lxml.html.document_fromstring(html_str)[0][0])
        return escaped_str
    else:
        html_str = u'<p>' + html_str + u'</p>'
        escaped_str = etree.tostring(lxml.html.document_fromstring(html_str)[0][0])
        return re.sub(r'^<p>|</p>$', '', escaped_str)


def html2latex(html, **kwargs):
    html = html.strip()
    if not html:
        return ''

    html = fix_encoding_of_html_using_lxml(html)

    html_to_be_hashed = u"{html}__{kwargs}".format(
        html=html,
        kwargs=kwargs
    )

    hashed_html = hash_string(html_to_be_hashed)

    latex_code = redis_client.get(hashed_html)

    if not latex_code:
        latex_code = _html2latex(html, **kwargs)
        redis_client.set(hashed_html, latex_code)

    return latex_code


def _html2latex(html, do_spellcheck=False, **kwargs):
    """
    Converts Html Element into LaTeX
    """

    # if "The nature of the roots of the quadratic equation" in html:
    #     import ipdb; ipdb.set_trace()

    # If html string has no text then don't need to do anything
    if not check_if_html_has_text(html):
        return ""

    # html = clean_paragraph_ending(html)

    html = html.replace("&uuml;", "\\checkmark")
    html = html.replace("&#252;", "\\checkmark")
    html = html.replace(u"ü", "\\checkmark")

    root = etree.HTML(html)
    body = root.find('.//body')

    content = u''.join([delegate(element, do_spellcheck=do_spellcheck, **kwargs)
                       for element in body])

    main_template = texenv.get_template('doc.tex')
    output = unicode(unescape(main_template.render(content=content))).encode(
        'utf-8').replace(r'& \\ \hline', r'\\ \hline')
    output = fix_formatting(output)

    output = re.sub(r"(?i)e\. g\.", "e.g.", output)
    output = re.sub(r"(?i)i\. e\.", "i.e.", output)

    for underscore in re.findall(r"s+_+|\s*_{2,}", output):
        output = output.replace(underscore, escape_latex(underscore), 1)

    output = re.sub(
        r"([a-zA-Z0-9]+)\s*\\begin\{textsupscript\}\s*(\w+)\s*\\end\{textsupscript\}",
        r"\\begin{math}\1^{\2}\\end{math}", output)
    output = re.sub(
        r"([a-zA-Z0-9]+)\s*\\begin\{textsubscript\}\s*(\w+)\s*\\end\{textsubscript\}",
        r"\\begin{math}\1_{\2}\\end{math}", output)

    output = output.decode("utf-8")
    items = (
        (u'\u2713', " \checkmark "),
        (u'\u009f', ""),
        (u'\u2715', u"\u00d7"),
        (u'\u2613', u"\u00d7"),
        (u'\u20b9', u"\\rupee"),
        (u'\u0086', u"¶"),
        (u'\u2012', u"-"),
        (u'\u25b3', u"∆"),
        (u'||', u'\\begin{math}\\parallel\\end{math}'),
        (u'\u03f5', u'\\epsilon '),
    )
    for oldvalue, newvalue in items:
        output = output.replace(oldvalue, newvalue)
    # output = re.sub(r"\\par\s*\\noindent", r"\\par\\noindent", output)
    # output = re.sub(r"(\\par\\noindent)+", r"\\par\\noindent", output)

    output = re.sub(r"\s+&\s+", r"\\&", output)

    output = output.replace("begin{bfseries}", "begin{bfseries} ")
    output = output.replace("\\end{bfseries}", " \\end{bfseries} ")
    output = output.replace("begin{underline}", "begin{underline} ")
    output = output.replace("\\end{underline}", " \\end{underline} ")

    output = re.sub(
        r"\\noindent\s*\\par",
        r"\\vspace{11pt}",
        output)

    output = output.replace(
        r'\end{math}\\textendash',
        r'\end{math}\textendash'
    )

    output = output.replace(
        r'\end{math}\\\textendash',
        r'\end{math}\textendash'
    )

    output = output.replace(
        r'\end{math}\\\\textendash',
        r'\end{math}\textendash'
    )

    output = output.replace(
        r'\end{math}\+',
        r'+ \end{math}'
    )

    output = output.replace(
        r'\end{math}\\+',
        r'+ \end{math}'
    )

    output = output.replace(
        r'\end{math}\\\+',
        r'+ \end{math}'
    )

    output = output.replace(
        r'\end{math}\\\\+',
        r'+ \end{math}'
    )

    output = output.replace(
        r'\end{math}\\-',
        r'- \end{math}'
    )

    output = output.replace(
        r'\end{math}\\\-',
        r'- \end{math}'
    )

    output = output.replace(
        r'\end{math}\\\\-',
        r'- \end{math}'
    )

    if r'\end{math}\\' in output:
        raise Exception

    return output.encode("utf-8")
