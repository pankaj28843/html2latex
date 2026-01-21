import pytest

from html2latex.utils import spellchecker

pytest.importorskip("enchant")

html = """
<html>
<body>

<h1>This is headin 1</h1>


</body>
</html>
"""


def test_get_word_checker():
    checker = spellchecker.get_word_checker("en_US")
    assert checker("wr000nggg") is True
    assert checker("correct") is False


def test_find_incorrect_words():
    wrong_text = "sume increct txt"
    checker = spellchecker.get_word_checker()
    wrong_words = set(spellchecker.find_incorrect_words(wrong_text, checker))
    assert wrong_words == {"increct", "sume", "txt"}


def test_check_spelling():
    wrong_text = "sum increct wurds"
    expected_output = (
        "sum \\textcolor{red}{\\Large \\textbf{increct}} \\textcolor{red}{\\Large \\textbf{wurds}}"
    )
    assert spellchecker.check_spelling(wrong_text) == expected_output


def test_check_spelling_in_html():
    output = (
        "\n<html>\n<body>\n\n<h1>This is"
        '<strong style="color: red; font-size: 14px;">headin</strong>1</h1>\n\n\n</body>\n</html>\n'
    )
    assert spellchecker.check_spelling_in_html(html) == output
