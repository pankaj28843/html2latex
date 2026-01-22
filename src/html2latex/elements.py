# -*- coding: utf-8 -*-
"""HTML element rendering primitives."""

from __future__ import annotations

import base64
import copy
import hashlib
import os
import re
import subprocess
import uuid

import jinja2

from .diagnostics import DiagnosticEvent, emit_diagnostic
from .helpers import capfirst
from .html_adapter import is_comment, parse_html
from .template_env import get_texenv
from .utils.html import check_if_html_has_text
from .utils.image import get_image_size
from .utils.text import (
    apply_inline_styles,
    clean,
    escape_latex,
    escape_tex_argument,
    parse_inline_style,
)
from .utils.unpack_merged_cells_in_table import unpack_merged_cells_in_table

_RE_MATH_SPLIT = re.compile(r"\r|\n")
_RE_MATH_OPEN = re.compile(r"^\\\s*\(", re.MULTILINE)
_RE_MATH_CLOSE = re.compile(r"\\\s*\)$", re.MULTILINE)
_RE_MATH_BRACE5 = re.compile(r"\{\{\{\{\{([\w,\.^]+)\}\}\}\}\}")
_RE_MATH_BRACE4 = re.compile(r"\{\{\{\{([\w,\.^]+)\}\}\}\}")
_RE_MATH_BRACE3 = re.compile(r"\{\{\{([\w,\.^]+)\}\}\}")
_RE_MATH_BRACE2 = re.compile(r"\{\{([\w,\.^]+)\}\}")
_RE_MULTI_SPACE = re.compile(r"( )+?")
_RE_PRE_OPEN = re.compile(r"^<pre[^>]*>", re.IGNORECASE)
_RE_PRE_CLOSE = re.compile(r"</pre>$", re.IGNORECASE)
_RE_TAGS = re.compile(r"<[^>]+>")
_RE_COL_WIDTH_PX = re.compile(r"width\s*:\s*([0-9]+)px", re.IGNORECASE)
_RE_COL_WIDTH_PCT = re.compile(r"width\s*:\s*([0-9\.]+)%", re.IGNORECASE)
_RE_COL_WIDTH_NUM = re.compile(r"width\s*:\s*([0-9\.]+)", re.IGNORECASE)
_RE_COL_WIDTH_SIMPLE = re.compile(r"width\s*:\s*(\d+)", re.IGNORECASE)
_RE_IMG_WIDTH_PX = re.compile(r"width:(\d+)px")
_RE_IMG_HEIGHT_PX = re.compile(r"height:(\d+)px")


def _spellcheck(text: str) -> str:
    # Resolve the function dynamically so tests can monkeypatch
    # html2latex.html2latex.check_spelling.
    from . import html2latex as api

    return api.check_spelling(text)


def delegate(element, do_spellcheck: bool = False, **kwargs):
    """
    Takes html element and converts it into string.
    """
    # delegate the work to classes handling special cases

    # Filter out empty tags
    try:
        element.tag
    except AttributeError:
        pass

    css_classes = element.attrib.get("class", "").lower()

    if element.tag == "div":
        my_element = HTMLElement(element, do_spellcheck, **kwargs)

    elif element.tag == "h1":
        my_element = H1(element, do_spellcheck, **kwargs)
    elif element.tag == "h2":
        my_element = H2(element, do_spellcheck, **kwargs)
    elif element.tag == "h3":
        my_element = H3(element, do_spellcheck, **kwargs)
    elif element.tag == "h4":
        my_element = H4(element, do_spellcheck, **kwargs)
    elif element.tag == "table":
        my_element = Table(element, do_spellcheck, **kwargs)
    elif element.tag == "tr":
        my_element = TR(element, do_spellcheck, **kwargs)
    elif element.tag == "td":
        my_element = TD(element, do_spellcheck, **kwargs)
    elif element.tag == "th":
        my_element = TH(element, do_spellcheck, **kwargs)
    elif element.tag == "img":
        try:
            my_element = IMG(element, do_spellcheck, **kwargs)
        except IOError as exc:
            emit_diagnostic(
                DiagnosticEvent(
                    code="asset/image-io-error",
                    category="asset",
                    severity="warn",
                    message=str(exc) or "Failed to load image asset.",
                    context={"src": element.attrib.get("src", "")},
                )
            )
            return ""
    elif element.tag == "a":
        my_element = A(element, do_spellcheck, **kwargs)
    elif element.tag == "span" and "math-tex" in css_classes:
        equation = element.text or ""
        tail = element.tail or ""

        equation = equation.strip()
        equation = " ".join(_RE_MATH_SPLIT.split(equation))
        equation = _RE_MATH_OPEN.sub("", equation)
        equation = _RE_MATH_CLOSE.sub("", equation)
        equation = _RE_MATH_BRACE5.sub(r"{\1}", equation)
        equation = _RE_MATH_BRACE4.sub(r"{\1}", equation)
        equation = _RE_MATH_BRACE3.sub(r"{\1}", equation)
        equation = _RE_MATH_BRACE2.sub(r"{\1}", equation)

        from html import unescape

        equation = unescape(equation)

        equation = equation.replace("&", "\\&")
        equation = equation.replace("<", "\\textless")
        equation = equation.replace(">", "\\textgreater")
        equation = equation.replace("\\;", "\\,")

        equation = equation.strip()

        if "\\\\" in equation and not equation.startswith("\\begin{gathered}"):
            equation = "\\begin{gathered}" + equation + "\\end{gathered}"

        equation = "\\begin{math}" + equation + "\\end{math}"
        _latex_code = equation + " " + tail
        return _latex_code

    elif is_comment(element):
        my_element = None  # skip XML comments
    else:
        # no special handling required
        my_element = HTMLElement(element, do_spellcheck, **kwargs)

    try:
        my_element
    except NameError:
        return ""

    if my_element is None:
        return ""
    return my_element.render()


class HTMLElement(object):
    def __init__(self, element, do_spellcheck: bool = False, **kwargs):
        self.element = element

        _html = self.element.to_html()

        self.has_content = check_if_html_has_text(_html)

        self.do_spellcheck = do_spellcheck

        self._init_kwargs = copy.deepcopy(kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)

        # we make a general dict to store the contents we send to the Jinja
        # templates.
        self.content = {}
        self.content["text"] = self.element.text if self.element.text is not None else ""
        self.content["tail"] = self.element.tail if self.element.tail is not None else ""
        self.content["tag"] = escape_latex(self.element.tag)

        """ Get attributes of the elements"""
        try:
            self.content["class"] = self.element.attrib["class"]
        except KeyError:
            self.content["class"] = ""
        for a in self.element.attrib:
            self.content[a] = self.element.attrib[a]

        style_map = parse_inline_style(self.element.attrib.get("style", ""))
        self.content["style_map"] = style_map
        css = self.element.attrib.get("style", "") or ""
        css = css.lower()
        text_alignment = kwargs.get("text_alignment")
        try:
            text_alignment = re.findall(
                r"text\-align\s*:\s*(\w+)",
                css,
                re.IGNORECASE,
            )[-1]
        except IndexError:
            # No text-align rule found in inline CSS; fall back to other sources.
            pass
        if not text_alignment and style_map.get("text-align"):
            text_alignment = style_map["text-align"]

        # If parent is <p> tag and it's center aligned then no need to align
        # children
        parent_element = self.element.getparent()
        if parent_element is not None and parent_element.tag == "p":
            if parent_element.attrib.get("text_alignment") == "center":
                text_alignment = None

        parent_element_tag = None
        if parent_element:
            parent_element_tag = parent_element.tag

        self.content["parent_element"] = parent_element
        self.content["parent_element_tag"] = parent_element_tag

        self.element.set("text_alignment", text_alignment or "")
        self._init_kwargs["text_alignment"] = self.content["text_alignment"] = text_alignment

        self.get_template()
        self.cap_first()
        self.fix_tail()
        self.escape_latex_characters()
        self.spell_check()
        self.apply_inline_styles()

        self.content["text"] = _RE_MULTI_SPACE.sub(" ", self.content["text"]).rstrip()

    def get_template(self):
        try:
            self.template = get_texenv().get_template(self.element.tag + ".tex")
        except jinja2.exceptions.TemplateNotFound:
            self.template = get_texenv().get_template("not_implemented.tex")
        except TypeError:
            self.template = get_texenv().get_template("error.tex")

    def cap_first(self):
        """Capitalize first alphabet of the element"""
        if not getattr(self, "CAPFIRST_ENABLED", False):
            return
        CAPFIRST_TAGS = (
            "li",
            "p",
            "td",
            "th",
        )
        if self.element.tag in CAPFIRST_TAGS:
            self.content["text"] = capfirst(self.content["text"])

    def fix_tail(self):
        """Fix tail of the element to include spaces accordingly"""
        tail = self.content["tail"]
        if (len(tail) > 0) and (tail[0] in [" ", "\t", "\r", "\n"]):
            tail = " " + tail.lstrip()
        if (len(tail) > 0) and (tail[-1] in [" ", "\t", "\r", "\n"]):
            tail = tail.rstrip() + " "
        self.content["tail"] = tail

    def spell_check(self):
        """Do spell check and highlight invalid words using enchant"""
        if self.do_spellcheck:
            self.content["text"] = _spellcheck(self.content["text"])
            self.content["tail"] = _spellcheck(self.content["tail"])
        else:
            pass

    def apply_inline_styles(self):
        if not self.content.get("style_map"):
            return
        if self.element.tag in {"span", "p", "div", "li", "td", "th", "a"}:
            self.content["text"] = apply_inline_styles(
                self.content["text"], self.content["style_map"]
            )

    def escape_latex_characters(self):
        """escape latex characters from text"""
        if self.element.tag == "pre":
            raw_text = self._extract_raw_text()
            self.content["text"] = raw_text

            tail = self.content["tail"]
            tail = clean(tail)
            tail = escape_latex(tail)
            self.content["tail"] = tail.replace("\r", "\n")
            return
        text = self.content["text"]
        text = clean(text)
        text = escape_latex(text)
        self.content["text"] = text.replace("\r", "\n")

        """escape latex characters from tail
        """
        tail = self.content["tail"]
        tail = clean(tail)
        tail = escape_latex(tail)
        self.content["tail"] = tail.replace("\r", "\n")

    def _extract_raw_text(self):
        html = self.element.to_html()
        html = _RE_PRE_OPEN.sub("", html)
        html = _RE_PRE_CLOSE.sub("", html)
        html = _RE_TAGS.sub("", html)
        from html import unescape as html_unescape

        return html_unescape(html)

    def render(self):
        self.render_children()
        latex_code = self.template.render(content=self.content)

        return latex_code

    def render_children(self):
        if self.element.tag == "pre":
            return
        if self.element.tag == "p":
            for child in self.element:
                if child.tag == "br":
                    self.content["text"] += "\\newline"
                    if child.tail:
                        tail = child.tail
                        if tail and not tail.startswith((" ", "\t", "\r", "\n")):
                            tail = " " + tail
                        self.content["text"] += tail
                else:
                    self.content["text"] += delegate(
                        child, do_spellcheck=self.do_spellcheck, **self._init_kwargs
                    )
        else:
            for child in self.element:
                self.content["text"] += delegate(
                    child, do_spellcheck=self.do_spellcheck, **self._init_kwargs
                )

    def remove_empty(self):
        """Must remove empty tags"""
        pass


class H1(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = get_texenv().get_template("h1.tex")


class H2(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = get_texenv().get_template("h2.tex")


class H3(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = get_texenv().get_template("h3.tex")


class H4(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        self.template = get_texenv().get_template("h4.tex")


class A(HTMLElement):
    """
    a href tag
    Gets the url stored in a href
    """

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        # make it a url if the 'href' attribute is set
        if "href" in element.attrib.keys():
            self.content["url"] = escape_tex_argument(element.attrib["href"])
        else:
            self.content["url"] = self.content["text"]


class Table(HTMLElement):
    def __init__(self, element, *args, **kwargs):
        super(Table, self).__init__(element, *args, **kwargs)

        if self.element.getprevious() is not None:
            self.content["has_previous_element"] = True
        else:
            self.content["has_previous_element"] = False

        if self.element.getnext() is not None:
            self.content["has_next_element"] = True
        else:
            self.content["has_next_element"] = False

        if not self.has_content:
            return

        _old_html = self.element.to_html()
        _new_html = unpack_merged_cells_in_table(_old_html)
        # Optional: Remove <strong> tags if you desire
        # _new_html = re.sub(r"<strong>|</strong>", "", _new_html)

        # Re-parse the table HTML after unpack_merged_cells_in_table
        parsed = parse_html(_new_html)
        tables = parsed.root.findall(".//table")
        if not tables:
            return
        self.element = element = tables[0]

        # Identify the row with the largest number of columns
        row_with_max_td = None
        max_td_count = 0
        for row in element.findall(".//tr"):
            col_count = len(row.findall(".//td")) + len(row.findall(".//th"))
            if col_count > max_td_count:
                row_with_max_td = row
                max_td_count = col_count

        # --------------------------------------------------
        # 1) Attempt to read col widths from <colgroup><col>
        # --------------------------------------------------
        col_widths = []
        col_elements = element.findall(".//colgroup/col")
        if col_elements:
            for col_el in col_elements:
                css = col_el.attrib.get("style", "")
                if not css:
                    col_widths.append(None)
                    continue
                # e.g., style="width: 10%;" or style="width: 50px;"
                match_px = _RE_COL_WIDTH_PX.search(css)
                match_pct = _RE_COL_WIDTH_PCT.search(css)
                match_num = _RE_COL_WIDTH_NUM.search(css)

                if match_px:
                    col_widths.append(float(match_px.group(1)))  # store px as float
                elif match_pct:
                    col_widths.append(float(match_pct.group(1)))  # store pct as float
                elif match_num:
                    col_widths.append(float(match_num.group(1)))  # e.g., width: 10
                else:
                    col_widths.append(None)
        else:
            # --------------------------------------------------
            # 2) Fallback: read widths from the row_with_max_td
            # --------------------------------------------------
            col_widths = []
            if row_with_max_td is not None:
                for td_element in row_with_max_td.iterchildren():
                    css = td_element.attrib.get("style", "")
                    if not css:
                        col_widths.append(None)
                        continue
                    try:
                        # e.g., style="width: 15"
                        _widths = _RE_COL_WIDTH_SIMPLE.findall(css)
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
            fraction = table_width_scaleup_factor * (col_width / total_width)
            _col_width_latex = r"%1.4f\linewidth" % fraction
            col_widths_in_latex.append(_col_width_latex)

            colspecifiers.append(r">{\raggedright\arraybackslash}p{%s}" % _col_width_latex)

        # Tag each cell in each row with the chosen col specs
        for row_index, row in enumerate(self.element.findall(".//tr")):
            # Zip to avoid index mismatch if the row has fewer or more cells
            for td, col_width_latex, colspecifier in zip(
                row.findall(".//td"), col_widths_in_latex, colspecifiers
            ):
                if td is None:
                    continue
                td.set("__colspecifier", colspecifier)
                td.set("__col_width_latex", col_width_latex)
                if row_index == 0:
                    td.set("is_first_row", "1")

        self.content["ncols"] = max_td_count
        self.content["cols"] = "|" + "|".join(colspecifiers) + "|"

        # Clean up text content
        self.content["text"] = self.content["text"].replace("\\par", " ")
        self.content["text"] = self.content["text"].replace("\n", "")
        self.content["text"] = self.content["text"].replace("\\hline\n\\\\", "\\hline ")

        # Set your LaTeX template
        self.template = get_texenv().get_template("table.tex")

    def render(self, *args, **kwargs):
        if not self.has_content:
            return ""
        latex_code = super(Table, self).render(*args, **kwargs)
        return latex_code


class TR(HTMLElement):
    """
    Rows in html table
    """

    def __init__(self, *args, **kwargs):
        obj = super(TR, self).__init__(*args, **kwargs)

        self.template = get_texenv().get_template("tr.tex")

        bottom_line_latex = ""

        for col_index, td in enumerate(self.element.iterchildren()):
            col_number = col_index + 1

            if td.attrib.get("__bottom_line"):
                bottom_line_latex += r"\cline{" + "{col}-{col}".format(col=col_number) + "}"

        self.content["bottom_line_latex"] = bottom_line_latex

        elements_to_be_deleted = []

        children = [x for x in self.element.iterchildren()]
        for col_index, td in enumerate(children):
            colspan = td.attrib.get("colspan") or td.attrib.get("_colspan")

            if colspan:
                colspan = int(colspan)
                _col_widths = [td.attrib.get("__col_width_latex")]

                for i in range(col_index + 1, col_index + colspan):
                    child = children[i]

                    _col_widths.append(child.attrib.get("__col_width_latex"))
                    elements_to_be_deleted.append(child)

                td.set("__col_width_latex", "+".join(_col_widths))

        for td in elements_to_be_deleted:
            self.element.remove(td)

        return obj


class TD(HTMLElement):
    """
    Columns in Html table
    """

    def __init__(self, *args, **kwargs):
        obj = super(TD, self).__init__(*args, **kwargs)

        self.template = get_texenv().get_template("td.tex")

        tr = self.element.getparent()
        is_first_row = tr.getprevious() is None

        self.content["is_first_row"] = is_first_row
        self.content["colspecifier"] = self.element.attrib.get("__colspecifier")
        self.content["col_width_latex"] = self.element.attrib.get("__col_width_latex")

        self.content["rowspan"] = self.element.attrib.get("rowspan") or self.element.attrib.get(
            "_rowspan"
        )
        self.content["colspan"] = self.element.attrib.get("colspan") or self.element.attrib.get(
            "_colspan"
        )

        return obj

    def render(self, *args, **kwargs):
        tr = self.element.getparent()
        is_first_row = tr.getprevious() is None
        is_last_column = self.element.getnext() is None

        self.content["is_first_row"] = is_first_row
        self.content["is_last_column"] = is_last_column

        latex_code = super(TD, self).render(*args, **kwargs)

        latex_code = re.sub(r"\s*\\par\s*", " ", latex_code)
        latex_code = re.sub(r"\s*\\par\s*\}\s*", " }", latex_code)

        return latex_code


class TH(TD):
    """
    Columns in Html table
    """

    def __init__(self, *args, **kwargs):
        obj = super(TH, self).__init__(*args, **kwargs)

        self.template = get_texenv().get_template("th.tex")

        return obj


class IMG(HTMLElement):
    is_table = False

    def __init__(self, element, *args, **kwargs):
        HTMLElement.__init__(self, element, *args, **kwargs)
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.get_image_link()
        self.image_size()

    def get_image_link(self):
        """get the link to the image and download it."""
        self.src = self.element.attrib["src"]

        # A Directory to store remote images.
        REMOTE_IMAGE_ROOT = "/var/tmp/html2latex-remote-images"
        GRAYSCALED_IMAGES = "/var/tmp/html2latex-grayscaled-images"

        # Make sure that directory exists.
        os.makedirs(REMOTE_IMAGE_ROOT, exist_ok=True)

        # Make sure that directory exists.
        os.makedirs(GRAYSCALED_IMAGES, exist_ok=True)

        # get the link to the image and download it.
        if self.src.startswith("http"):
            output_filename = re.sub(r"[^A-Za-z0-9\.]", "-", self.src)
            if len(output_filename) > 128:
                output_filename = hashlib.sha512(output_filename).hexdigest()
            output_filepath = os.path.normpath(os.path.join(REMOTE_IMAGE_ROOT, output_filename))

            _, ext = os.path.splitext(output_filepath)
            if not ext:
                output_filepath = output_filepath + ".png"

            if not os.path.isfile(output_filepath):
                p = subprocess.Popen(
                    ["wget", "-c", "-O", output_filepath, self.src], cwd=REMOTE_IMAGE_ROOT
                )
                p.wait()
                if not os.path.isfile(output_filepath):
                    raise Exception("Could not download the image file: {}.".format(self.src))

            self.src = self.element.attrib["src"] = output_filepath

        try:
            CONVERT_IMAGE_TO_GRAYSCALE = self.CONVERT_IMAGE_TO_GRAYSCALE
        except AttributeError:
            CONVERT_IMAGE_TO_GRAYSCALE = False

        if CONVERT_IMAGE_TO_GRAYSCALE is True:
            jpg_filename = "".join(os.path.splitext(self.src)[:-1])
            jpg_filepath = os.path.normpath(
                os.path.join(
                    GRAYSCALED_IMAGES,
                    hashlib.sha512(
                        jpg_filename.encode() if isinstance(jpg_filename, str) else jpg_filename
                    ).hexdigest()
                    + "_grayscaled.jpg",
                )
            )
            # if not os.path.isfile(jpg_filepath):
            tmp_filepath_1 = "/tmp/{}.jpg".format(str(uuid.uuid4()))
            p = subprocess.Popen(
                [
                    "convert",
                    self.src,
                    "-background",
                    "white",
                    "-alpha",
                    "remove",
                    "-colorspace",
                    "cmyk",
                    tmp_filepath_1,
                ]
            )
            p.wait()

            tmp_filepath_2 = "/tmp/{}.jpg".format(str(uuid.uuid4()))
            p = subprocess.Popen(["convert", tmp_filepath_1, "-type", "Grayscale", tmp_filepath_2])
            p.wait()
            p = subprocess.Popen(
                [
                    "convert",
                    tmp_filepath_2,
                    "-background",
                    "white",
                    "-alpha",
                    "remove",
                    "-colorspace",
                    "cmyk",
                    jpg_filepath,
                ]
            )
            p.wait()

            self.src = self.element.attrib["src"] = jpg_filepath

        self.style = self.element.attrib.get("style", "")

    def image_size(self):
        """Adjust image size according to requirements"""
        img_width = None
        img_height = None

        match_width = _RE_IMG_WIDTH_PX.search(self.style)
        if match_width:
            img_width = int(float(match_width.group(1)) * 0.75)

        match_height = _RE_IMG_HEIGHT_PX.search(self.style)
        if match_height:
            img_height = int(float(match_height.group(1)) * 0.75)

        try:
            if img_width is None or img_height is None:
                width, height = get_image_size(self.src)
                img_width = 3.0 / 4 * width
                img_height = 3.0 / 4 * height
        except IOError:
            raise

        self.content["imagename"] = escape_tex_argument(self.src)
        self.content["imagewidth"], self.content["imageheight"] = img_width, img_height

        self.template = get_texenv().get_template("img.tex")

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
            self.template = get_texenv().get_template("img_base64_encoded_string.tex")
        else:
            context = {
                "content": self.content,
                "ALIGN_IMAGE_IN_CENTER": ALIGN_IMAGE_IN_CENTER,
            }

        output = self.template.render(**context)
        return output
