# -*- coding: utf-8 -*-
from __future__ import unicode_literals

# Standard Library
from unittest import TestCase

# HTML2LaTeX Stuff
from html2latex.utils import text


class TestUtilsText(TestCase):

    def test_clean(self):
        function = text.clean

        items = (
            (u"sad\u00c2", u'sad '),
            (u'sadas\u00c2', u'sadas '),
            (u"Â Goal!!", u'  Goal!!'),
            (u'â Goal!!', ' Goal!!'),
            (u'â Goal!', '\' Goal!'),
            (u'â Super', ' Super'),
            (u'â Super!', ' Super!'),

        )
        for value, output in items:
            self.assertEqual(function(value), output)

    def test_clean_paragraph_ending(self):
        function = text.clean_paragraph_ending

        items = (
            ("""<p>he scored a goal  &nbsp; </p>""",
             '<p>he scored a goal</p>'),
            ("""<p>What a Goal!!<br></p>""", '<p>What a Goal!!</p>'),
            ("""<p>Goal!!! &nbsp;</p><br>""", '<p>Goal!!!</p><br>'),
            ("""<br><p>Goal!!! &nbsp;</p><br>""",
             '<br><p>Goal!!! &nbsp;</p><br>'),

        )
        for value, output in items:
            self.assertEqual(function(value), output)

    def test_fix_text(self):
        function = text.fix_text

        items = (
            ("Working Function,Create new function.",
             'Working Function, Create new function. '),
            ("12213,21.12", u'12213,21.12'),
            ("12213a,21.12", u'12213a, 21.12'),
            ("for football .4 meter is a good measure.So,is this one.",
             u'for football. 4 meter is a good measure. So, is this one. '),


        )
        for value, output in items:
            self.assertEqual(function(value), output)

    def test_fix_formatting(self):
        function = text.fix_formatting

        items = (
            ("Working   : Function", 'Working: Function'),
            ("Working   ; Function;", 'Working; Function; '),
            ("Who is SRT  ?    ", 'Who is SRT? '),
            ("TM scored > 2 goals", 'TM scored \\textgreater  2 goals'),
            ("TM scored < 2 goals", 'TM scored \\textless  2 goals'),
            ("TM scored &gt; 2 goals", 'TM scored \\textgreater  2 goals'),
            ("TM scored &lt; 2 goals", 'TM scored \\textless  2 goals'),
            (" TM'            scored &gt; 2 goals ' ",
             " TM `scored \\textgreater  2 goals' "),
            (" TM scored  2 goals \par ", ' TM scored  2 goals '),


        )
        for value, output in items:
            self.assertEqual(function(value), output)
