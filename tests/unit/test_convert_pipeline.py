from html2latex.ast import HtmlDocument, HtmlElement, HtmlText
from html2latex.latex import LatexCommand, LatexEnvironment, LatexRaw, LatexText
from html2latex.rewrite_pipeline import convert_document


def test_convert_paragraph_and_inline():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="p",
                children=(
                    HtmlText(text="Hello "),
                    HtmlElement(tag="strong", children=(HtmlText(text="World"),)),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexText)
    assert latex.body[0].text == "Hello "
    assert isinstance(latex.body[1], LatexCommand)
    assert latex.body[1].name == "textbf"
    assert isinstance(latex.body[2], LatexCommand)
    assert latex.body[2].name == "par"


def test_convert_heading():
    doc = HtmlDocument(children=(HtmlElement(tag="h1", children=(HtmlText(text="Title"),)),))
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexCommand)
    assert latex.body[0].name == "section"


def test_convert_div_and_hr():
    doc = HtmlDocument(
        children=(
            HtmlElement(tag="div", children=(HtmlText(text="Block"),)),
            HtmlElement(tag="hr"),
        )
    )
    latex = convert_document(doc)
    assert latex.body[0].text == "Block"
    assert latex.body[1].name == "par"
    assert latex.body[2].name == "hrule"


def test_convert_inline_code_sup_sub():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="p",
                children=(
                    HtmlElement(tag="code", children=(HtmlText(text="x"),)),
                    HtmlElement(tag="sup", children=(HtmlText(text="2"),)),
                    HtmlElement(tag="sub", children=(HtmlText(text="i"),)),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    assert latex.body[0].name == "texttt"
    assert latex.body[1].name == "textsuperscript"
    assert latex.body[2].name == "textsubscript"
    assert latex.body[3].name == "par"


def test_convert_unordered_list():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="ul",
                children=(
                    HtmlElement(tag="li", children=(HtmlText(text="A"),)),
                    HtmlElement(tag="li", children=(HtmlText(text="B"),)),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert env.name == "itemize"
    assert env.children[0].name == "item"
    assert env.children[1].text == "A"
    assert env.children[2].name == "item"
    assert env.children[3].text == "B"


def test_convert_description_list():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="dl",
                children=(
                    HtmlElement(tag="dt", children=(HtmlText(text="Term"),)),
                    HtmlElement(tag="dd", children=(HtmlText(text="Definition"),)),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert env.name == "description"
    assert env.children[0].name == "item"
    assert env.children[0].options == ("Term",)
    assert env.children[1].text == "Definition"


def test_convert_link_and_image():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="p",
                children=(
                    HtmlElement(
                        tag="a",
                        attrs={"href": "https://example.com?q=1&v=2"},
                        children=(HtmlText(text="Link"),),
                    ),
                    HtmlElement(tag="img", attrs={"src": "/img.png"}),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    link = latex.body[0]
    assert isinstance(link, LatexCommand)
    assert link.name == "href"
    assert link.args[0].children[0].text == "https://example.com?q=1&v=2"
    assert link.args[1].children[0].text == "Link"
    image = latex.body[1]
    assert image.name == "includegraphics"
    assert image.args[0].children[0].text == "/img.png"
    assert latex.body[2].name == "par"


def test_convert_link_without_label_uses_url():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="a",
                attrs={"href": "https://example.com"},
                children=(),
            ),
        )
    )
    latex = convert_document(doc)
    link = latex.body[0]
    assert link.name == "url"
    assert link.args[0].children[0].text == "https://example.com"


def test_convert_blockquote():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="blockquote",
                children=(HtmlElement(tag="p", children=(HtmlText(text="Quote"),)),),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert env.name == "quote"
    assert env.children[0].text == "Quote"
    assert env.children[1].name == "par"


def test_convert_preformatted_block():
    doc = HtmlDocument(
        children=(HtmlElement(tag="pre", children=(HtmlText(text="line1\nline2"),)),)
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert env.name == "verbatim"
    assert env.children[0].value == "line1\nline2"


def test_convert_inline_math_tex():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="span",
                attrs={"class": "math-tex"},
                children=(HtmlText(text="\\(x+1\\)"),),
            ),
        )
    )
    latex = convert_document(doc)
    assert latex.body[0].value == "\\(x+1\\)"


def test_convert_display_math_tex():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="div",
                attrs={"class": "math-tex"},
                children=(HtmlText(text="x+1"),),
            ),
        )
    )
    latex = convert_document(doc)
    assert latex.body[0].value == "\\[x+1\\]"


def test_convert_math_from_data_attribute():
    doc = HtmlDocument(
        children=(HtmlElement(tag="span", attrs={"data-latex": "x^2"}, children=()),)
    )
    latex = convert_document(doc)
    assert latex.body[0].value == "\\(x^2\\)"


def test_convert_table_basic():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="table",
                children=(
                    HtmlElement(
                        tag="tr",
                        children=(
                            HtmlElement(tag="td", children=(HtmlText(text="A"),)),
                            HtmlElement(tag="td", children=(HtmlText(text="B"),)),
                        ),
                    ),
                    HtmlElement(
                        tag="tr",
                        children=(
                            HtmlElement(tag="td", children=(HtmlText(text="C"),)),
                            HtmlElement(tag="td", children=(HtmlText(text="D"),)),
                        ),
                    ),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert isinstance(env, LatexEnvironment)
    assert env.name == "tabular"
    assert env.args[0].children[0].text == "ll"
    assert isinstance(env.children[0], LatexRaw)
    assert env.children[0].value == "A & B \\\\"
    assert env.children[1].value == "C & D \\\\"


def test_convert_table_with_colspan_and_headers():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="table",
                children=(
                    HtmlElement(
                        tag="tr",
                        children=(
                            HtmlElement(tag="th", children=(HtmlText(text="Head"),)),
                            HtmlElement(tag="th", children=(HtmlText(text="Right"),)),
                        ),
                    ),
                    HtmlElement(
                        tag="tr",
                        children=(
                            HtmlElement(
                                tag="td",
                                attrs={"colspan": "2"},
                                children=(HtmlText(text="Wide"),),
                            ),
                            HtmlElement(tag="td", children=(HtmlText(text="Tail"),)),
                        ),
                    ),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert env.args[0].children[0].text == "lll"
    assert env.children[0].value == "\\textbf{Head} & \\textbf{Right} & \\\\"
    assert env.children[1].value == "\\multicolumn{2}{l}{Wide} & Tail \\\\"
