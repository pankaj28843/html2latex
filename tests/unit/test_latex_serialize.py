from html2latex.latex import (
    LatexCommand,
    LatexDocumentAst,
    LatexEnvironment,
    LatexGroup,
    LatexRaw,
    LatexText,
    infer_packages,
    serialize_document,
)
from html2latex.latex.serialize import _group_text, _serialize_node


def test_serialize_text_escapes_special_chars():
    doc = LatexDocumentAst(body=(LatexText(text="A&B%$#_{}~^\\"),))
    output = serialize_document(doc)
    assert output == "A\\&B\\%\\$\\#\\_\\{\\}\\textasciitilde{}\\textasciicircum{}\\textbackslash{}"


def test_serialize_command_with_group():
    group = LatexGroup(children=(LatexText(text="Hello"),))
    cmd = LatexCommand(name="textbf", args=(group,))
    doc = LatexDocumentAst(body=(cmd,))
    assert serialize_document(doc) == "\\textbf{Hello}"


def test_serialize_environment():
    env = LatexEnvironment(
        name="itemize",
        children=(LatexCommand(name="item"), LatexText(text="A")),
    )
    doc = LatexDocumentAst(body=(env,))
    assert serialize_document(doc) == "\\begin{itemize}\\item A\\end{itemize}"


def test_serialize_raw_passthrough():
    doc = LatexDocumentAst(body=(LatexRaw(value="A & B \\\\"),))
    assert serialize_document(doc) == "A & B \\\\"


def test_serialize_group_in_body():
    doc = LatexDocumentAst(body=(LatexGroup(children=(LatexText(text="X"),)),))
    assert serialize_document(doc) == "{X}"


def test_serialize_command_with_options_no_args():
    doc = LatexDocumentAst(body=(LatexCommand(name="item", options=("label",)),))
    assert serialize_document(doc) == "\\item[label] "


def test_infer_packages_inside_group():
    group = LatexGroup(children=(LatexCommand(name="href"),))
    doc = LatexDocumentAst(body=(group,))
    assert infer_packages(doc) == {"hyperref"}


def test_serialize_unknown_node_returns_empty():
    assert _serialize_node(object()) == ""


def test_infer_packages_from_ast():
    href = LatexCommand(
        name="href",
        args=(
            LatexGroup(children=(LatexText(text="https://example.com"),)),
            LatexGroup(children=(LatexText(text="link"),)),
        ),
    )
    img = LatexCommand(name="includegraphics")
    table = LatexEnvironment(name="tabularx")
    doc = LatexDocumentAst(body=(href, img, table))
    assert infer_packages(doc) == {"hyperref", "graphicx", "tabularx"}


def test_infer_packages_xcolor_from_colorbox():
    colorbox = LatexCommand(
        name="colorbox",
        args=(
            LatexGroup(children=(LatexText(text="yellow"),)),
            LatexGroup(children=(LatexText(text="text"),)),
        ),
    )
    doc = LatexDocumentAst(body=(colorbox,))
    assert infer_packages(doc) == {"xcolor"}


def test_infer_packages_array_from_tabular_spec():
    spec = LatexGroup(children=(LatexRaw(value=r">{\centering\arraybackslash}p{0.5\textwidth}"),))
    table = LatexEnvironment(name="tabular", args=(spec,))
    doc = LatexDocumentAst(body=(table,))
    assert "array" in infer_packages(doc)


def test_group_text_supports_latextext():
    group = LatexGroup(children=(LatexText(text=r">{\centering\arraybackslash}p{1cm}"),))
    assert _group_text(group) == r">{\centering\arraybackslash}p{1cm}"
