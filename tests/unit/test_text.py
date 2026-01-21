import pytest

from html2latex.utils import text


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("some backslashes \\", "some backslashes \\textbackslash "),
        ("&_#{lol}", "\\&\\_\\#\\{lol\\}"),
        ("%$lol", "\\%\\$lol"),
        ("~lol", "\\~lol"),
        ("^foo", "\\^foo"),
        ('"bar"', "''bar''"),
        ("..text..", "..text.."),
        (r"....text....", "\\ldots text\\ldots "),
        ("5 > 4", r"5 \textgreater  4"),
        ("3 &gt; 2", r"3 \textgreater  2"),
        ("4 < 5", r"4 \textless  5"),
        ("7 &lt; 10", r"7 \textless  10"),
        ("2 &degree; 3", r"2 \degree  3"),
    ],
)
def test_escape_tex(value, expected):
    assert text.escape_tex(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("some backslashes \\", "some backslashes \\textbackslash "),
        ("&_#{lol}", "\\&\\_\\#\\{lol\\}"),
        ("%$lol", "\\%\\$lol"),
        ("~lol", "\\~lol"),
        ('"bar"', "''bar''"),
        ("..text..", "..text.."),
        (r"....text....", "\\ldots text\\ldots "),
        ("5 > 4", r"5 \textgreater  4"),
        ("4 < 5", r"4 \textless  5"),
        ("2 &degree; 3", r"2 \degree  3"),
    ],
)
def test_unescape_latex(value, expected):
    assert text.unescape_latex(expected) == value


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Jack & Jill", "Jack \\& Jill"),
        ("some numbers #1 #2 #3", "some numbers \\#1 \\#2 \\#3"),
        ("python_methods", "python\\underline{\\thickspace}methods"),
        ("10/20=50\\%", "10/20=50\\%"),
        ("15/20=75%", "15/20=75\\%"),
        ("foo \\rm", "foo \\mathrm"),
    ],
)
def test_escape_latex(value, expected):
    assert text.escape_latex(value) == expected


def test_unescape():
    value = "A&nbsp;B &amp; &#x41; &#65;"
    assert text.unescape(value) == "A\\hspace{1pt}B & A A"
