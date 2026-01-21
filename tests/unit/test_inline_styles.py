import pytest

from html2latex.utils.text import apply_inline_styles, parse_inline_style


@pytest.mark.parametrize(
    ("style", "expected"),
    [
        ("font-weight: bold;", {"font-weight": "bold"}),
        ("font-style: italic;", {"font-style": "italic"}),
        (
            "color: #ff00ff; background-color: yellow;",
            {"color": "#ff00ff", "background-color": "yellow"},
        ),
    ],
)
def test_parse_inline_style(style, expected):
    assert parse_inline_style(style) == expected


def test_apply_inline_styles_bold_italic():
    styles = {"font-weight": "bold", "font-style": "italic"}
    assert apply_inline_styles("Text", styles) == "\\textit{\\textbf{Text}}"


def test_apply_inline_styles_underline_strike():
    styles = {"text-decoration": "underline line-through"}
    assert apply_inline_styles("Text", styles) == "\\sout{\\underline{Text}}"


def test_apply_inline_styles_color_hex():
    styles = {"color": "#ff0000"}
    assert apply_inline_styles("Text", styles) == "\\textcolor[HTML]{FF0000}{Text}"


def test_apply_inline_styles_color_named_and_bg():
    styles = {"color": "red", "background-color": "yellow"}
    assert apply_inline_styles("Text", styles) == "\\colorbox{yellow}{\\textcolor{red}{Text}}"
