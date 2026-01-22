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
