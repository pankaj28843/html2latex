from __future__ import unicode_literals

from unittest import TestCase

from html2latex.utils import text


class TestUtilsText(TestCase):

    def test_clean(self):
        function = text.clean

        items = (
            (u"sad\u00c2", u'sad '),
            (u'sadas\u00c2', u'sadas '),
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

        )
        for value, output in items:
            self.assertEqual(function(value), output)
