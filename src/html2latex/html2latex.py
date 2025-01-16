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
import sys
import uuid
import logging

# Third Party Stuff
import jinja2
from lxml import etree
from lxml.html import document_fromstring
from xamcheck_utils.html import check_if_html_has_text
from xamcheck_utils.text import unicodify

from .setup_texenv import setup_texenv
from .utils.unpack_merged_cells_in_table import unpack_merged_cells_in_table
from .utils.html_table import render_html
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

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
    format='%(asctime)s %(levelname)s %(name)s: %(message)s'
)
logger = logging.getLogger(__name__)

capfirst = lambda x: x and x[0].upper() + x[1:]

loader = jinja2.FileSystemLoader(
    os.path.dirname(os.path.realpath(__file__)) + '/templates')
texenv = setup_texenv(loader)

VERSION = "0.0.63"
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
    logger.info("Delegating work to classes handling special cases, tag: {}".format(element.tag))

    if element.tag == 'div':
        my_element = HTMLElement(element, do_spellcheck, **kwargs)

    elif element.tag == 'h1':
        my_element = H1(element, do_spellcheck, **kwargs)
    elif element.tag == 'h2':
        my_element = H2(element, do_spellcheck, **kwargs)
    elif element.tag == 'h3':
        my_element = H3(element, do_spellcheck, **kwargs)
    elif element.tag == 'h4':
        my_element = H4(element, do_spellcheck, **kwargs)
    elif element.tag == 'table':
        my_element = Table(element, do_spellcheck, **kwargs)
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
        self.escape_latex_characters()
        self.spell_check()

        def fix_spaces(self, match):
            group = match.groups()[0] or ""
            group = group.replace(" ", "\\,")
            return " " + group + " "

        self.content['text'] = re.sub(
            r'( )+?', ' ', self.content['text']).rstrip()

    def get_template(self):
        logger.info("Getting template for tag: {}".format(self.element.tag))
        try:
            self.template = texenv.get_template(self.element.tag + '.tex')
        except jinja2.exceptions.TemplateNotFound:
            logger.info("Template not found for tag: {}".format(self.element.tag))
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
        tail = self.content['tail']
        if (len(tail) > 0) and (tail[0] in [' \t\r\n']):
            tail = ' ' + tail.lstrip()
        if (len(tail) > 0) and (tail[-1] in [' \t\r\n']):
            tail = tail.rstrip() + ' '
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
        self.content['text'] = text.replace("\r", "\n")

        """escape latex characters from tail
        """
        tail = self.content['tail']
        tail = clean(tail)
        tail = escape_latex(tail)
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


class H1(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = texenv.get_template('h1.tex')


class H2(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = texenv.get_template('h2.tex')


class H3(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = texenv.get_template('h3.tex')


class H4(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = texenv.get_template('h4.tex')


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
        super(Table, self).__init__(element, *args, **kwargs)

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
        # Optional: Remove <strong> tags if you desire
        # _new_html = re.sub(r"<strong>|</strong>", "", _new_html)

        # Re-parse the table HTML after unpack_merged_cells_in_table
        self.element = element = etree.HTML(_new_html).findall('.//table')[0]

        # Identify the row with the largest number of columns
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
            etree.tostring(body_element).strip()
        ).strip()
        rendered_html = render_html(complete_html_string)

        unique_id = str(uuid.uuid4())
        html_file = u"/tmp/html2latex_table_{0}.html".format(unique_id)
        with open(html_file, "wb") as f:
            f.write(rendered_html)

        url = u"file://{0}".format(html_file)

        # --------------------------------------------------
        # 1) Attempt to read col widths from <colgroup><col>
        # --------------------------------------------------
        col_widths = []
        col_elements = element.findall('.//colgroup/col')
        if col_elements:
            for col_el in col_elements:
                css = col_el.attrib.get('style', '')
                if not css:
                    col_widths.append(None)
                    continue
                # e.g., style="width: 10%;" or style="width: 50px;"
                match_px = re.search(r'width\s*:\s*([0-9]+)px', css, re.IGNORECASE)
                match_pct = re.search(r'width\s*:\s*([0-9\.]+)%', css, re.IGNORECASE)
                match_num = re.search(r'width\s*:\s*([0-9\.]+)', css, re.IGNORECASE)

                if match_px:
                    col_widths.append(float(match_px.group(1)))  # store px as float
                elif match_pct:
                    col_widths.append(float(match_pct.group(1))) # store pct as float
                elif match_num:
                    col_widths.append(float(match_num.group(1))) # e.g., width: 10
                else:
                    col_widths.append(None)
        else:
            # --------------------------------------------------
            # 2) Fallback: read widths from the row_with_max_td
            # --------------------------------------------------
            col_widths = []
            if row_with_max_td is not None:
                for td_element in row_with_max_td.iterchildren():
                    css = td_element.attrib.get('style', '')
                    if not css:
                        col_widths.append(None)
                        continue
                    try:
                        # e.g., style="width: 15"
                        _widths = re.findall(r'width\s*:\s*(\d+)', css, re.IGNORECASE)
                        width = _widths[0]
                        col_widths.append(float(width))
                    except (IndexError, ValueError):
                        col_widths.append(None)

        # -----------------------------------------------------------------------
        # 3) If we have no valid widths (all None, or empty), use a simple heuristic
        # -----------------------------------------------------------------------
        if not col_widths or all(w is None for w in col_widths):
            # Heuristic: just distribute columns evenly, so each "column width" = 1
            # We'll treat these as relative widths below
            col_widths = [1.0 for _ in range(max_td_count)]
        else:
            # If some columns have None, replace with a simple heuristic, e.g. average
            valid_widths = [w for w in col_widths if w is not None]
            if valid_widths:
                avg = sum(valid_widths) / len(valid_widths)
            else:
                avg = 1.0
            col_widths = [w if w is not None else avg for w in col_widths]

        total_width = sum(col_widths)
        if total_width == 0:
            # Avoid division by zero
            total_width = 1.0

        # Compute col specifiers
        colspecifiers = []
        table_width_scaleup_factor = 0.85

        col_widths_in_latex = []
        for col_width in col_widths:
            # fraction of total (scaled by factor)
            fraction = (table_width_scaleup_factor * (col_width / total_width))
            _col_width_latex = r'%1.4f\linewidth' % fraction
            col_widths_in_latex.append(_col_width_latex)

            colspecifiers.append(r">{\raggedright\arraybackslash}p{%s}" % _col_width_latex)

        # Tag each cell in each row with the chosen col specs
        for row_index, row in enumerate(self.element.findall('.//tr')):
            # Zip to avoid index mismatch if the row has fewer or more cells
            for td, col_width_latex, colspecifier in zip(
                row.findall('.//td'),
                col_widths_in_latex,
                colspecifiers
            ):
                if td is None:
                    continue
                td.set('__colspecifier', colspecifier)
                td.set('__col_width_latex', col_width_latex)
                if row_index == 0:
                    td.set('is_first_row', "1")

        self.content['ncols'] = max_td_count
        self.content['cols'] = '|' + '|'.join(colspecifiers) + '|'

        # Clean up text content
        self.content['text'] = self.content['text'].replace('\\par', ' ')
        self.content['text'] = self.content['text'].replace('\n', '')
        self.content['text'] = self.content['text'].replace('\\hline\n\\\\', '\\hline ')

        # Set your LaTeX template
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

        latex_code = re.sub(r'\s*\\par\s*', ' ', latex_code)
        latex_code = re.sub(r'\s*\\par\s*\}\s*', ' }', latex_code)

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


def fix_encoding_of_html_using_lxml(html):
    fixed_html = re.sub(
        r'^<body>|</body>$',
        "",
        etree.tostring(document_fromstring(html)[0])
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
    return _html2latex(html, **kwargs)


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
