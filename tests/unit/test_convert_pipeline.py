from html2latex.ast import HtmlDocument, HtmlElement, HtmlText
from html2latex.latex import LatexCommand, LatexEnvironment, LatexRaw, LatexText
from html2latex.pipeline import convert_document
from html2latex.pipeline.convert import _convert_node


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


def test_convert_description_list_keeps_pending_label():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="dl",
                children=(
                    HtmlText(text="ignored"),
                    HtmlElement(tag="dt", children=(HtmlText(text="Lonely"),)),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert env.children[0].name == "item"
    assert env.children[0].options == ("Lonely",)


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


def test_convert_anchor_without_href_flattens_children():
    doc = HtmlDocument(children=(HtmlElement(tag="a", children=(HtmlText(text="Plain"),)),))
    latex = convert_document(doc)
    assert latex.body[0].text == "Plain"


def test_convert_image_without_src_uses_alt_text():
    doc = HtmlDocument(children=(HtmlElement(tag="img", attrs={"alt": "Alt text"}, children=()),))
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexText)
    assert latex.body[0].text == "Alt text"


def test_convert_unknown_tag_flattens_children():
    doc = HtmlDocument(children=(HtmlElement(tag="custom", children=(HtmlText(text="Inside"),)),))
    latex = convert_document(doc)
    assert latex.body[0].text == "Inside"


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


def test_convert_empty_math_returns_nothing():
    doc = HtmlDocument(children=(HtmlElement(tag="span", attrs={"class": "math-tex"}),))
    latex = convert_document(doc)
    assert latex.body == ()


def test_convert_math_tag_inline():
    doc = HtmlDocument(children=(HtmlElement(tag="math", children=(HtmlText(text="x+1"),)),))
    latex = convert_document(doc)
    assert latex.body[0].value == "\\(x+1\\)"


def test_convert_math_block_delimiters():
    doc = HtmlDocument(
        children=(
            HtmlElement(tag="span", attrs={"data-latex": "$$x$$"}, children=()),
            HtmlElement(tag="span", attrs={"data-latex": "$y$"}, children=()),
            HtmlElement(tag="span", attrs={"data-latex": "\\[z\\]"}, children=()),
        )
    )
    latex = convert_document(doc)
    assert latex.body[0].value == "\\[x\\]"
    assert latex.body[1].value == "\\(y\\)"
    assert latex.body[2].value == "\\[z\\]"


def test_convert_math_data_attribute_branch():
    doc = HtmlDocument(children=(HtmlElement(tag="span", attrs={"data-math": "z"}, children=()),))
    latex = convert_document(doc)
    assert latex.body[0].value == "\\(z\\)"


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


def test_convert_table_skips_non_rows():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="table",
                children=(HtmlText(text="ignore"), HtmlElement(tag="tr", children=())),
            ),
        )
    )
    latex = convert_document(doc)
    assert latex.body == ()


def test_convert_table_with_invalid_colspan_defaults_to_one():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="table",
                children=(
                    HtmlElement(
                        tag="tr",
                        children=(
                            HtmlElement(
                                tag="td",
                                attrs={"colspan": "bad"},
                                children=(HtmlText(text="A"),),
                            ),
                            HtmlElement(tag="td", children=(HtmlText(text="B"),)),
                        ),
                    ),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert env.args[0].children[0].text == "ll"
    assert env.children[0].value == "A & B \\\\"


def test_convert_table_caption_skips_non_element_children():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="table",
                children=(
                    HtmlText(text="note"),
                    HtmlElement(tag="caption", children=(HtmlText(text="Title"),)),
                    HtmlElement(
                        tag="tr",
                        children=(HtmlElement(tag="td", children=(HtmlText(text="Cell"),)),),
                    ),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    env = latex.body[0]
    assert isinstance(env, LatexEnvironment)
    assert env.name == "table"
    assert isinstance(env.children[0], LatexCommand)
    assert env.children[0].name == "caption"


def test_convert_table_without_rows_returns_empty():
    doc = HtmlDocument(children=(HtmlElement(tag="table", children=()),))
    latex = convert_document(doc)
    assert latex.body == ()


def test_convert_node_ignores_unknown_type():
    assert _convert_node(object()) == []


def test_convert_empty_figure():
    doc = HtmlDocument(children=(HtmlElement(tag="figure", children=()),))
    latex = convert_document(doc)
    assert latex.body == ()


def test_convert_figure_text_only():
    doc = HtmlDocument(children=(HtmlElement(tag="figure", children=(HtmlText(text="text"),)),))
    latex = convert_document(doc)
    assert latex.body == ()


def test_convert_orphan_figcaption():
    doc = HtmlDocument(
        children=(HtmlElement(tag="figcaption", children=(HtmlText(text="Caption"),)),)
    )
    latex = convert_document(doc)
    assert latex.body[0].text == "Caption"


def test_convert_figure_caption_multi_para():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="figure",
                children=(
                    HtmlElement(
                        tag="figcaption",
                        children=(
                            HtmlElement(tag="p", children=(HtmlText(text="Para 1"),)),
                            HtmlElement(tag="p", children=(HtmlText(text="Para 2"),)),
                        ),
                    ),
                ),
            ),
        )
    )
    latex = convert_document(doc)
    # Should produce figure environment with caption, and \par replaced by space
    assert isinstance(latex.body[0], LatexEnvironment)
    assert latex.body[0].name == "figure"


def test_convert_small_tag():
    doc = HtmlDocument(children=(HtmlElement(tag="small", children=(HtmlText(text="small"),)),))
    latex = convert_document(doc)
    assert len(latex.body) == 3
    assert latex.body[0].value == r"{\small "
    assert latex.body[1].text == "small"
    assert latex.body[2].value == "}"


def test_convert_center_tag():
    doc = HtmlDocument(children=(HtmlElement(tag="center", children=(HtmlText(text="centered"),)),))
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexEnvironment)
    assert latex.body[0].name == "center"
    assert latex.body[0].children[0].text == "centered"


def test_convert_p_text_align_center():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="p",
                attrs={"style": "text-align: center"},
                children=(HtmlText(text="centered"),),
            ),
        )
    )
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexEnvironment)
    assert latex.body[0].name == "center"


def test_convert_p_text_align_right():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="p",
                attrs={"style": "text-align: right"},
                children=(HtmlText(text="right"),),
            ),
        )
    )
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexEnvironment)
    assert latex.body[0].name == "flushright"


def test_convert_p_text_align_left():
    doc = HtmlDocument(
        children=(
            HtmlElement(
                tag="p",
                attrs={"style": "text-align:left"},
                children=(HtmlText(text="left"),),
            ),
        )
    )
    latex = convert_document(doc)
    assert isinstance(latex.body[0], LatexEnvironment)
    assert latex.body[0].name == "flushleft"


def test_convert_semantic_inline_elements():
    # ins -> underline
    doc = HtmlDocument(children=(HtmlElement(tag="ins", children=(HtmlText(text="inserted"),)),))
    latex = convert_document(doc)
    assert latex.body[0].name == "underline"

    # kbd -> texttt
    doc = HtmlDocument(children=(HtmlElement(tag="kbd", children=(HtmlText(text="key"),)),))
    latex = convert_document(doc)
    assert latex.body[0].name == "texttt"

    # samp -> texttt
    doc = HtmlDocument(children=(HtmlElement(tag="samp", children=(HtmlText(text="sample"),)),))
    latex = convert_document(doc)
    assert latex.body[0].name == "texttt"

    # var -> textit
    doc = HtmlDocument(children=(HtmlElement(tag="var", children=(HtmlText(text="variable"),)),))
    latex = convert_document(doc)
    assert latex.body[0].name == "textit"

    # cite -> textit
    doc = HtmlDocument(children=(HtmlElement(tag="cite", children=(HtmlText(text="citation"),)),))
    latex = convert_document(doc)
    assert latex.body[0].name == "textit"


def test_convert_mark_tag():
    doc = HtmlDocument(
        children=(HtmlElement(tag="mark", children=(HtmlText(text="highlighted"),)),)
    )
    latex = convert_document(doc)
    assert latex.body[0].name == "colorbox"
    # First arg is color (yellow)
    assert latex.body[0].args[0].children[0].text == "yellow"
    # Second arg is the content
    assert latex.body[0].args[1].children[0].text == "highlighted"


def test_convert_big_tag():
    doc = HtmlDocument(children=(HtmlElement(tag="big", children=(HtmlText(text="large"),)),))
    latex = convert_document(doc)
    assert len(latex.body) == 3
    assert latex.body[0].value == r"{\large "
    assert latex.body[1].text == "large"
    assert latex.body[2].value == "}"
