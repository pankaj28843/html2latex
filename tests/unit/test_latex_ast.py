from html2latex.latex import (
    LatexCommand,
    LatexDocumentAst,
    LatexEnvironment,
    LatexGroup,
    LatexText,
)


def test_latex_ast_construction():
    text = LatexText(text="hello")
    group = LatexGroup(children=(text,))
    command = LatexCommand(name="textbf", args=(group,))
    env = LatexEnvironment(name="itemize", children=(command,))
    doc = LatexDocumentAst(preamble=(), body=(env,), metadata={"lang": "en"})

    assert doc.body[0].name == "itemize"
    assert doc.body[0].children[0].name == "textbf"
    assert doc.metadata["lang"] == "en"
