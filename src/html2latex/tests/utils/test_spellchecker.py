from __future__ import unicode_literals
from unittest import TestCase
from html2latex.utils import spellchecker

html = """
<html>
<body>

<h1>This is headin 1</h1>


</body>
</html>
"""


class TestSpellChecker(TestCase):

    def test_get_word_checker(self):
        checker = spellchecker.get_word_checker()
        self.assertEqual(True, checker('lol'))
        self.assertEqual(False, checker('word'))

        german_checker = spellchecker.get_word_checker('de_DE')
        self.assertEqual(True, german_checker('lol'))
        self.assertEqual(False, german_checker("Guten"))

    def test_find_incorrect_words(self):
        wrong_text = "sume increct txt"
        checker = spellchecker.get_word_checker()
        wrong_word_list = ['increct', 'sume', 'txt']
        self.assertEqual(
            wrong_word_list, spellchecker.find_incorrect_words(wrong_text, checker))

    def test_check_spelling(self):
        wrong_text = "sum increct wurds"
        expected_output = 'sum \\textcolor{red}{\\Large \\textbf{increct}} \\textcolor{red}{\\Large \\textbf{wurds}}'
        self.assertEqual(
            expected_output, spellchecker.check_spelling(wrong_text))

    def test_check_spelling_in_html(self):
        output = u'\n<html>\n<body>\n\n<h1>This is<strong style="color: red; font-size: 14px;">headin</strong>1</h1>\n\n\n</body>\n</html>\n'

        self.assertEqual(spellchecker.check_spelling_in_html(html), output)
