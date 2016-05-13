# -*- coding: utf-8 -*-
"""
Convert HTML generated from CKEditor to LaTeX environment.
"""
# Standard Library
import base64
import copy
import hashlib
import hmac
import os
import re
import subprocess
import uuid

# Third Party Stuff
import jinja2
import lxml
import mmh3
import redis
import splinter
from lxml import etree
from PIL import Image
from repoze.lru import lru_cache
from xamcheck_utils.html import check_if_html_has_text
from xamcheck_utils.text import unicodify

from .setup_texenv import setup_texenv
from .utils.unpack_merged_cells_in_table import unpack_merged_cells_in_table
from .utils.html_table import get_image_for_html_table, render_html
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

VERSION = "0.0.68"
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)
CAPFIRST_ENABLED = False
# Templates for each class here.


def get_width_of_element_by_xpath(browser, xpath):
    javascript_code = """
    document.evaluate('{xpath}', document, null,\
        XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.offsetWidth;
    """.format(xpath=xpath).strip()

    return browser.evaluate_script(javascript_code)


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

    css_classes = element.attrib.get('class', '').lower()

    if element.tag == 'div':
        my_element = HTMLElement(element, do_spellcheck, **kwargs)

    elif element.tag == 'table':
        USE_IMAGE_FOR_TABLE = kwargs.get('USE_IMAGE_FOR_TABLE', False)
        table_inner_html = u''.join([etree.tostring(e) for e in element])

        if not USE_IMAGE_FOR_TABLE:
            my_element = Table(element, do_spellcheck, **kwargs)
        else:
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
    elif element.tag == 'td':
        my_element = TD(element, do_spellcheck, **kwargs)
    elif element.tag == 'img':
        try:
            my_element = IMG(element, do_spellcheck, **kwargs)
        except IOError:
            return ''
    elif element.tag == 'a':
        my_element = A(element, do_spellcheck, **kwargs)
    elif element.tag == 'span' and 'math-tex' in css_classes:
        equation = element.text or ''
        tail = element.tail or ''
        tail = clean(tail)
        tail = escape_tex(tail)
        tail = tail.replace("\r", "\n")

        equation = equation.strip()
        equation = " ".join(re.split(r"\r|\n", equation))
        equation = re.sub(r'^\\\s*\(', "", equation, re.MULTILINE)
        equation = re.sub(r'\\\s*\)$', "", equation, re.MULTILINE)
        equation = re.sub(
            r"\{\{\{\{\{([\w,\.^]+)\}\}\}\}\}", r"{\1}", equation)
        equation = re.sub(r"\{\{\{\{([\w,\.^]+)\}\}\}\}", r"{\1}", equation)
        equation = re.sub(r"\{\{\{([\w,\.^]+)\}\}\}", r"{\1}", equation)
        equation = re.sub(r"\{\{([\w,\.^]+)\}\}", r"{\1}", equation)

        from HTMLParser import HTMLParser
        html_parser = HTMLParser()
        equation = html_parser.unescape(equation)

        equation = equation.replace("&", "\&")
        equation = equation.replace("<", "\\textless")
        equation = equation.replace(">", "\\textgreater")
        equation = equation.replace("\;", "\,")

        equation = equation.strip()

        if "\\\\" in equation and not equation.startswith("\\begin{gathered}"):
            equation = "\\begin{gathered}" + equation + "\\end{gathered}"

        equation = "\\begin{math}" + equation + "\\end{math}"
        _latex_code = equation + ' ' + tail
        return _latex_code

    elif isinstance(element, etree._Comment):
        my_element = None  # skip XML comments
    else:
        # no special handling required
        my_element = HTMLElement(element, do_spellcheck, **kwargs)

    try:
        my_element
    except NameError:
        return ''

    if my_element is None:
        return ''
    else:
        return my_element.render()


class HTMLElement(object):

    def __init__(self, element, do_spellcheck=False, **kwargs):
        self.element = element

        # try:
        #     if self.element.tag == 'p' and self.element.getparent().tag == 'td':
        #         import ipdb; ipdb.set_trace()
        # except:
        #     pass

        _html = etree.tounicode(self.element)

        self.has_content = check_if_html_has_text(_html)

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
        self.escape_latex_characters()

        """ Get attributes of the elements"""
        try:
            self.content['class'] = self.element.attrib['class']
        except KeyError:
            self.content['class'] = ''
        for a in self.element.attrib:
            self.content[a] = self.element.attrib[a]

        css = self.element.attrib.get('style', '') or ''
        css = css.lower()
        text_alignment = kwargs.get('text_alignment')
        try:
            text_alignment = re.findall(
                r'text\-align\s*:\s*(\w+)',
                css,
                re.IGNORECASE)[-1]
        except:
            pass

        # If parent is <p> tag and it's center aligned then no need to align
        # children
        parent_element = self.element.getparent()
        if parent_element is not None and parent_element.tag == 'p':
            if parent_element.attrib.get('text_alignment') == 'center':
                text_alignment = None

        parent_element_tag = None
        if parent_element:
            parent_element_tag = parent_element.tag

        self.content['parent_element'] = parent_element
        self.content['parent_element_tag'] = parent_element_tag

        self.element.set('text_alignment', text_alignment or '')
        self._init_kwargs["text_alignment"] = self.content["text_alignment"] = text_alignment

        self.get_template()
        self.cap_first()
        self.fix_tail()
        self.spell_check()

        def fix_spaces(self, match):
            group = match.groups()[0] or ""
            group = group.replace(" ", "\\,")
            return " " + group + " "

        self.content['text'] = re.sub(
            r'( )+?', ' ', self.content['text'])

    def get_template(self):
        try:
            self.template = texenv.get_template(self.element.tag + '.tex')
        except jinja2.exceptions.TemplateNotFound:
            self.template = texenv.get_template('not_implemented.tex')
        except TypeError:
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
        return
        # tail = self.content['tail']
        # if (len(tail) > 0) and (tail[0] in [' \t\r\n']):
        #     tail = ' ' + tail.lstrip()
        # if (len(tail) > 0) and (tail[-1] in [' \t\r\n']):
        #     tail = tail.rstrip() + ' '
        # self.content['tail'] = tail

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
        text = escape_tex(text)

        text = text.replace(u'\u00a0', '\\,')
        text = text.replace(u'\u00c2', '\\,')

        self.content['text'] = text.replace("\r", "\n")

        """escape latex characters from tail
        """
        tail = self.content['tail']
        tail = clean(tail)
        tail = escape_tex(tail)
        tail = tail.replace(u'\u00a0', '\\,')
        tail = tail.replace(u'\u00c2', '\\,')

        self.content['tail'] = tail.replace("\r", "\n")

    def render(self):
        self.render_children()
        latex_code = self.template.render(content=self.content)

        return latex_code

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

        if self.element.getprevious() is not None:
            self.content['has_previous_element'] = True
        else:
            self.content['has_previous_element'] = False

        if self.element.getnext() is not None:
            self.content['has_next_element'] = True
        else:
            self.content['has_next_element'] = False

        if not self.has_content:
            return

        _old_html = etree.tounicode(self.element)

        _new_html = unpack_merged_cells_in_table(_old_html)
        # _new_html = re.sub(r"<strong>|</strong>", "", _new_html)

        self.element = element = etree.HTML(_new_html).findall('.//table')[0]

        row_with_max_td = None
        max_td_count = 0

        for row in element.findall('.//tr'):
            col_count = len(row.findall('.//td')) + len(row.findall('.//th'))

            if col_count > max_td_count:
                row_with_max_td = row
                max_td_count = col_count

        tree = element.getroottree()
        body_element = tree.find(".//table").getroottree().find(".//body")
        complete_html_string = re.sub(
            r'^<body>|</body>$',
            '',
            lxml.etree.tostring(body_element).strip()
        ).strip()
        rendered_html = render_html(complete_html_string)

        unique_id = str(uuid.uuid4())
        html_file = u"/tmp/html2latex_table_{0}.html".format(unique_id)
        with open(html_file, "wb") as f:
            f.write(rendered_html)

        url = u"file://{0}".format(html_file)

        col_widths = []
        for td_element in row_with_max_td.iterchildren():
            css = td_element.attrib.get('style', '')
            if not css:
                col_widths.append(None)
                break

            try:
                _widths = re.findall(
                    r'width\s*:\s*(\d+)',
                    css,
                    re.IGNORECASE)
                width = _widths[0]
            except IndexError:
                col_widths.append(None)
                break

            width = float(width)
            col_widths.append(width)

        if not col_widths or None in col_widths:
            with splinter.Browser('phantomjs') as browser:
                browser.visit(url)

                col_widths = []
                for _element in row_with_max_td.getchildren():
                    if _element.tag == "td" or _element.tag == "th":
                        xpath = tree.getpath(_element)
                        width = get_width_of_element_by_xpath(browser, xpath)

                        col_widths.append(width)

        total_width = sum(col_widths)

        colspecifiers = []

        table_width_scaleup_factor = 0.85
        self.content["table_width_scaleup_factor"] = table_width_scaleup_factor

        col_widths_in_latex = []
        for col_width in col_widths:
            _col_width_latex = r'%1.4f\linewidth' % (
                float(table_width_scaleup_factor) * float(float(col_width) / float(total_width))
            )
            colspecifier = r">{\raggedright\arraybackslash}p{%s}" % _col_width_latex

            col_widths_in_latex.append(_col_width_latex)
            colspecifiers.append(colspecifier)

        first_row = self.element.findall('.//tr')[0]

        for _index, row in enumerate(self.element.findall('.//tr')):
            for td, col_width_latex, colspecifier in zip(row.findall('.//td'), col_widths_in_latex, colspecifiers):
                if td is None:
                    continue

                td.set('__colspecifier', colspecifier)
                td.set('__col_width_latex', col_width_latex)

                if _index == 0:
                    td.set('is_first_row', "1")

        self.content['ncols'] = max_td_count

        self.content['cols'] = '|' + '|'.join(colspecifiers) + '|'

        # self.content['text'] = self.content['text'].replace('\\par', ' ')
        # self.content['text'] = self.content['text'].replace('\n', '')
        # self.content['text'] = self.content[
        #     'text'].replace('\\hline\n\\\\', '\\hline ')

        self.template = texenv.get_template('table.tex')

    def render(self, *args, **kwargs):
        if not self.has_content:
            return ''

        latex_code = super(Table, self).render(*args, **kwargs)

        return latex_code


class TR(HTMLElement):

    """
    Rows in html table
    """

    def __init__(self, *args, **kwargs):
        obj = super(TR, self).__init__(*args, **kwargs)

        self.template = texenv.get_template('tr.tex')

        bottom_line_latex = ''

        for (col_index, td) in enumerate(self.element.iterchildren()):
            col_number = col_index + 1

            if td.attrib.get('__bottom_line'):
                bottom_line_latex += (
                    r'\cline{' + '{col}-{col}'.format(col=col_number) + '}')

        self.content['bottom_line_latex'] = bottom_line_latex

        elements_to_be_deleted = []

        children = [x for x in self.element.iterchildren()]
        for (col_index, td) in enumerate(children):
            colspan = td.attrib.get('colspan') or td.attrib.get('_colspan')

            if colspan:
                colspan = int(colspan)
                _col_widths = [td.attrib.get('__col_width_latex')]

                for i in range(col_index + 1, col_index + colspan):
                    child = children[i]

                    _col_widths.append(child.attrib.get('__col_width_latex'))
                    elements_to_be_deleted.append(child)

                td.set("__col_width_latex", '+'.join(_col_widths))

        for td in elements_to_be_deleted:
            self.element.remove(td)

        return obj


class TD(HTMLElement):
    """
    Columns in Html table
    """

    def __init__(self, *args, **kwargs):
        obj = super(TD, self).__init__(*args, **kwargs)

        self.template = texenv.get_template('td.tex')

        tr = self.element.getparent()
        is_first_row = tr.getprevious() is None

        self.content['is_first_row'] = is_first_row
        self.content['colspecifier'] = self.element.attrib.get('__colspecifier')
        self.content['col_width_latex'] = self.element.attrib.get('__col_width_latex')

        self.content['rowspan'] = self.element.attrib.get('rowspan') or self.element.attrib.get('_rowspan')
        self.content['colspan'] = self.element.attrib.get('colspan') or self.element.attrib.get('_colspan')

        return obj

    def render(self, *args, **kwargs):

        tr = self.element.getparent()
        is_first_row = tr.getprevious() is None
        is_last_column = self.element.getnext() is None

        self.content['is_first_row'] = is_first_row
        self.content['is_last_column'] = is_last_column

        latex_code = super(TD, self).render(*args, **kwargs)

        # latex_code = re.sub(r'\s*\\par\s*', ' ', latex_code)
        # latex_code = re.sub(r'\s*\\par\s*\}\s*', ' }', latex_code)

        return latex_code


class TH(TD):

    """
    Columns in Html table
    """

    def __init__(self, *args, **kwargs):
        obj = super(TH, self).__init__(*args, **kwargs)

        self.template = texenv.get_template('th.tex')

        return obj


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
            output_filepath = os.path.normpath(
                os.path.join(
                    REMOTE_IMAGE_ROOT,
                    output_filename))

            if not os.path.splitext(output_filepath):
                output_filepath = output_filepath + ".png"

            if not os.path.isfile(output_filepath):
                p = subprocess.Popen(
                    ["wget", "-c", "-O", output_filepath, self.src], cwd=REMOTE_IMAGE_ROOT)
                p.wait()
                if not os.path.isfile(output_filepath):
                    raise Exception("Count not download the image file: {}.".format(self.src))

            self.src = self.element.attrib['src'] = output_filepath

        try:
            CONVERT_IMAGE_TO_GRAYSCALE = self.CONVERT_IMAGE_TO_GRAYSCALE
        except AttributeError:
            CONVERT_IMAGE_TO_GRAYSCALE = False

        if CONVERT_IMAGE_TO_GRAYSCALE is True:
            jpg_filename = ''.join(os.path.splitext(self.src)[:-1])
            jpg_filepath = os.path.normpath(os.path.join(
                GRAYSCALED_IMAGES,
                hashlib.sha512(jpg_filename).hexdigest() + '_grayscaled.jpg',
            ))
            jpg_filepath = '/tmp/{}.jpg'.format(str(uuid.uuid4()))

            # if not os.path.isfile(jpg_filepath):
            tmp_filepath_1 = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
            p = subprocess.Popen(
                ['convert', self.src, '-background', 'white', '-alpha',
                 'remove', '-colorspace', 'cmyk', tmp_filepath_1]
            )
            p.wait()

            tmp_filepath_2 = '/tmp/{}.jpg'.format(str(uuid.uuid4()))
            p = subprocess.Popen(
                ['convert', tmp_filepath_1, '-type', 'Grayscale',
                 tmp_filepath_2]
            )
            p.wait()
            p = subprocess.Popen(
                ['convert', tmp_filepath_2, '-background', 'white', '-alpha',
                 'remove', '-colorspace', 'cmyk',
                 jpg_filepath]
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
        except IOError as e:
            raise

        self.content['imagename'] = self.src
        self.content['imagewidth'], self.content[
            'imageheight'] = img_width, img_height

        self.template = texenv.get_template('img.tex')

    def render(self):
        try:
            ALIGN_IMAGE_IN_CENTER = self.ALIGN_IMAGE_IN_CENTER
        except AttributeError:
            ALIGN_IMAGE_IN_CENTER = False

        try:
            USE_BASE64_ENCODED_STRING_FOR_IMAGE = self.USE_BASE64_ENCODED_STRING_FOR_IMAGE
        except AttributeError:
            USE_BASE64_ENCODED_STRING_FOR_IMAGE = False

        if USE_BASE64_ENCODED_STRING_FOR_IMAGE is True:
            filename, file_extension = os.path.splitext(self.src)

            jobname_base64 = "%s.base64" % uuid.uuid4()
            jobname_tmp_image = "%s%s" % (uuid.uuid4(), file_extension)

            with open(self.src, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read())

            context = {
                "content": self.content,
                "jobname": jobname_base64,
                "image_filepath": jobname_tmp_image,
                "encoded_string": encoded_string,
                "ALIGN_IMAGE_IN_CENTER": ALIGN_IMAGE_IN_CENTER,
            }
            self.template = texenv.get_template('img_base64_encoded_string.tex')
        else:
            context = {
                "content": self.content,
                "ALIGN_IMAGE_IN_CENTER": ALIGN_IMAGE_IN_CENTER,
            }

        output = self.template.render(**context)
        return output


@lru_cache(512)
def hash_string(s):
    return "html2latex_{version}_{mmh3_hash}_{hmac_of_sha512_hash}".format(
        version=VERSION,
        mmh3_hash=mmh3.hash128(s),
        hmac_of_sha512_hash=hmac.new(hashlib.sha512(s).hexdigest()).hexdigest(),
    )


def fix_encoding_of_html_using_lxml(html):
    fixed_html = re.sub(
        r'^<body>|</body>$',
        "",
        etree.tostring(lxml.html.document_fromstring(html)[0])
    ).strip()

    if re.search(r'^<p>', html) is None:
        fixed_html = re.sub(
            r'^<p>',
            "",
            fixed_html
        )
    if re.search(r'</p>$', html) is None:
        fixed_html = re.sub(
            r'</p>$',
            "",
            fixed_html
        )

    return fixed_html


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
    # If html string has no text then don't need to do anything
    if not check_if_html_has_text(html):
        return ""

    html = html.replace("&uuml;", "\\checkmark")
    html = html.replace("&#252;", "\\checkmark")
    html = html.replace(u"ü", "\\checkmark")

    root = etree.HTML(html)
    body = root.find('.//body')

    line_separator = kwargs.get('LINE_SPERATOR', '')

    content = line_separator.join([delegate(element, do_spellcheck=do_spellcheck, **kwargs)
                       for element in body])

    # main_template = texenv.get_template('doc.tex')
    # output = unicode(unescape(main_template.render(content=content))).encode(
    #     'utf-8').replace(r'& \\ \hline', r'\\ \hline ')
    # output = fix_formatting(output)

    output = content

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

    if not isinstance(output, unicode):
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
