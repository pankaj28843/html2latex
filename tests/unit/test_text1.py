import pytest

from html2latex.utils import text


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("sad\u00c2", "sad "),
        ("sadas\u00c2", "sadas "),
        ("Â Goal!!", "  Goal!!"),
        ("â Goal!!", " Goal!!"),
        ("â Goal!", "' Goal!"),
        ("â Super", " Super"),
        ("â Super!", " Super!"),
    ],
)
def test_clean(value, expected):
    assert text.clean(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("<p>he scored a goal  &nbsp; </p>", "<p>he scored a goal</p>"),
        ("<p>What a Goal!!<br></p>", "<p>What a Goal!!</p>"),
        ("<p>Goal!!! &nbsp;</p><br>", "<p>Goal!!!</p><br>"),
        ("<br><p>Goal!!! &nbsp;</p><br>", "<br><p>Goal!!! &nbsp;</p><br>"),
    ],
)
def test_clean_paragraph_ending(value, expected):
    assert text.clean_paragraph_ending(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Working Function,Create new function.", "Working Function, Create new function. "),
        ("12213,21.12", "12213,21.12"),
        ("12213a,21.12", "12213a, 21.12"),
        (
            "for football .4 meter is a good measure.So,is this one.",
            "for football. 4 meter is a good measure. So, is this one. ",
        ),
    ],
)
def test_fix_text(value, expected):
    assert text.fix_text(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("Working   : Function", "Working: Function"),
        ("Working   ; Function;", "Working; Function; "),
        ("Who is SRT  ?    ", "Who is SRT? "),
        ("TM scored > 2 goals", "TM scored \\textgreater  2 goals"),
        ("TM scored < 2 goals", "TM scored \\textless  2 goals"),
        ("TM scored &gt; 2 goals", "TM scored \\textgreater  2 goals"),
        ("TM scored &lt; 2 goals", "TM scored \\textless  2 goals"),
        (" TM'            scored &gt; 2 goals ' ", " TM `scored \\textgreater  2 goals' "),
        (" TM scored  2 goals \\par ", " TM scored  2 goals "),
    ],
)
def test_fix_formatting(value, expected):
    assert text.fix_formatting(value) == expected
