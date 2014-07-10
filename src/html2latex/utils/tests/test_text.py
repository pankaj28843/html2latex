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
