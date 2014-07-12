# -*- coding: utf-8 -*-
"""
Convert HTML generated from CKEditor to LaTeX environment.
Improved structure as per the guidelines given in the  below link.  
http://docs.python-guide.org/en/latest/writing/structure/
"""
import os
import re

import setup_texenv
import utils
import PIL
import jinja2
import lxml
import xamcheck


capfirst = lambda x: x and x[0].upper() + x[1:]

loader = jinja2.FileSystemLoader(
    os.path.dirname(os.path.realpath(__file__)) + '/templates')
texenv = setup_texenv.setup_texenv(loader)

CAPFIRST_ENABLED = True
# Templates for each class here.


def delegate(element, do_spellcheck=False):
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
        my_element = HTMLElement(element, do_spellcheck)

    # elif element.tag == 'table':
    #     my_element = Table(element, do_spellcheck)
    elif element.tag == 'table':
        table_inner_html = u''.join([lxml.etree.tostring(e) for e in element])
        items = (
                ("&#13;", ""),
                ("&uuml;", "&#10003;"),
                ("&#252;", "&#10003;"),
                ("\\checkmark", "&#10003;"),
                (u"ü", "&#10003;"),

        )
        for oldvalue, newvalue in items:
            table_inner_html = table_inner_html.replace(oldvalue, newvalue)

        image_file = utils.get_image_for_html_table(
            table_inner_html, do_spellcheck=do_spellcheck)

        new_html = u"<img src='{0}'/>".format(image_file)
        new_element = lxml.etree.HTML(new_html).find(".//img")
        my_element = IMG(new_element, is_table=True)
        my_element.content["is_table"] = True
    elif element.tag == 'tr':
        my_element = TR(element, do_spellcheck)
    elif element.tag == 'tdr':
        my_element = TD(element, do_spellcheck)
    elif element.tag == 'img':
        try:
            my_element = IMG(element, do_spellcheck)
        except IOError:
            return ''
    elif element.tag == 'a':
        my_element = A(element, do_spellcheck)
    elif isinstance(element, lxml.etree._Comment):
        my_element = None  # skip XML comments
    else:
        # no special handling required
        my_element = HTMLElement(element, do_spellcheck)

    try:
        my_element
    except NameError:
        # error_message(u"Error with element!! %s\n\n" %
        #               lxml.etree.tostring(element), terminate=False)
        return ''

    if my_element is None:
        return ''
    else:
        return my_element.render()


class HTMLElement(object):

    def __init__(self, element, do_spellcheck=False):
        self.element = element
        self.do_spellcheck = do_spellcheck

        # we make a general dict to store the contents we send to the Jinja
        # templates.
        self.content = {}
        self.content[
            'text'] = self.element.text if self.element.text is not None else ''
        self.content[
            'tail'] = self.element.tail if self.element.tail is not None else ''
        self.content['tag'] = utils.escape_latex(self.element.tag)

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
            self.content['text'] = utils.check_spelling(self.content['text'])
            self.content['tail'] = utils.check_spelling(self.content['tail'])
        else:
            pass

    def escape_latex_characters(self):
        """escape latex characters from text
        """
        text = self.content['text']
        text = utils.clean(text)
        text = utils.escape_latex(text)
        text = utils.fix_text(text)
        self.content['text'] = text.replace("\r", "\n")

        """escape latex characters from tail
        """
        tail = self.content['tail']
        tail = utils.clean(tail)
        tail = utils.escape_latex(tail)
        tail = utils.fix_text(tail)
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
                        child, do_spellcheck=self.do_spellcheck)
        else:
            for child in self.element:
                self.content['text'] += delegate(
                    child, do_spellcheck=self.do_spellcheck)

    def remove_empty(self):
        '''Must remove empty tags'''
        pass


class A(HTMLElement):

    """
    a href tag
    Gets the url stored in a href   
    """

    def __init__(self, element):
        HTMLElement.__init__(self, element)
        # make it a url if the 'href' attribute is set
        if 'href' in element.attrib.keys():
            self.content['url'] = element.attrib['href']
        else:
            self.content['url'] = self.content['text']


class Table(HTMLElement):

    def __init__(self, element):
        HTMLElement.__init__(self, element)
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

    def __init__(self, element):
        HTMLElement.__init__(self, element)
        self.template = texenv.get_template('tr.tex')


class TD(HTMLElement):

    """
    Columns in Html table
    """

    def __init__(self, element):
        HTMLElement.__init__(self, element)
        self.template = texenv.get_template('td.tex')


class IMG(HTMLElement):
    is_table = False

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.get_image_link()
        self.image_size()

    def get_image_link(self):
        """get the link to the image and download it."""
        self.src = self.element.attrib['src']
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
                width, height = utils.get_image_size(self.src)
                img_width = 3. / 4 * width
                img_height = 3. / 4 * height
            if not self.is_table:
                image = PIL.Image.open(self.src)
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
        output = self.template.render(content=self.content)
        # output = "\\begin{center}" + output + "\end{center}"
        return output


def html2latex(html, do_spellcheck=False):
    """
    Converts Html Element into LaTeX
    """
    # If html string has no text then don't need to do anything
    if not xamcheck.utils.html.check_if_html_has_text(html):
        return ""

    html = utils.clean_paragraph_ending(html)
    html = html.replace("&uuml;", "\\checkmark")
    html = html.replace("&#252;", "\\checkmark")
    html = html.replace(u"ü", "\\checkmark")

    root = lxml.etree.HTML(html)
    body = root.find('.//body')

    content = u''.join([delegate(element, do_spellcheck=do_spellcheck)
                       for element in body])
    main_template = texenv.get_template('doc.tex')
    output = unicode(utils.unescape(main_template.render(content=content))).encode(
        'utf-8').replace(r'& \\ \hline', r'\\ \hline')
    output = utils.fix_formatting(output)

    output = re.sub(r"(?i)e\. g\.", "e.g.", output)
    output = re.sub(r"(?i)i\. e\.", "i.e.", output)

    for underscore in re.findall(r"s+_+|\s*_{2,}", output):
        output = output.replace(underscore, utils.escape_latex(underscore), 1)

    output = re.sub(
        r"([a-zA-Z0-9]+)\\begin\{textsupscript\}\s*(\w+)\s*\\end\{textsupscript\}",
        r"\\begin{math}\1^{\2}\\end{math}", output)
    output = re.sub(
        r"([a-zA-Z0-9]+)\\begin\{textsubscript\}\s*(\w+)\s*\\end\{textsubscript\}",
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
        (u'||', u'\\begin{math}\\parallel\\end{math}')
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

    return output.encode("utf-8")
