from __future__ import unicode_literals

# Standard Library
from unittest import TestCase

# HTML2LaTeX Stuff
from html2latex.utils import text


class TestText(TestCase):

    def test_escape_tex(self):
        items = (
                ('some backslashes \\', 'some backslashes \\textbackslash '),
                ('&_#{lol}', '\&\\_\\#\\{lol\\}'),
                ('%$lol', '\%\\$lol'),
                ('~lol', '\~lol'),
                ('^foo', '\^foo'),
                ('"bar"', "''bar''"),
                ('..text..', '..text..'),
                (r'....text....', '\\ldots text\\ldots '),
                (u'5 > 4', r"5 \textgreater  4"),
                (u'3 &gt; 2', r"3 \textgreater  2"),
                (u'4 < 5', r"4 \textless  5"),
                (u'7 &lt; 10', r"7 \textless  10"),
                (u'2 &degree; 3', r"2 \degree  3"),
        )
        for value, output in items:
            self.assertEqual(text.escape_tex(value), output)

    def test_unescape_latex(self):
        items = (
                ('some backslashes \\', 'some backslashes \\textbackslash '),
                ('&_#{lol}', '\&\\_\\#\\{lol\\}'),
                ('%$lol', '\%\\$lol'),
                ('~lol', '\~lol'),
                ('"bar"', "''bar''"),
                ('..text..', '..text..'),
                (r'....text....', '\\ldots text\\ldots '),
                (u'5 > 4', r"5 \textgreater  4"),
                (u'4 < 5', r"4 \textless  5"),
                (u'2 &degree; 3', r"2 \degree  3"),
        )
        for value, output in items:
            self.assertEqual(
                text.unescape_latex(output), value)

    def test_escape_latex(self):
        items = (
                ('Jack & Jill', 'Jack \& Jill'),
                ('some numbers #1 #2 #3', 'some numbers \#1 \#2 \#3'),
                ('python_methods', 'python\\underline{\\thickspace}methods'),
                ('10/20=50\\%', '10/20=50\\%'),
                ('15/20=75%', '15/20=75\\%'),
                ('foo \\rm', 'foo \\mathrm'),
        )
        for value, output in items:
            self.assertEqual(text.escape_latex(value), output)
