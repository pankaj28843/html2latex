from __future__ import unicode_literals

from unittest import TestCase
from os.path import abspath, dirname, join, normpath
from html2latex.utils.image import get_image_size

CURRENT_DIR = dirname(abspath(__file__))
IMAGE_FILE_ROOT = normpath(join(CURRENT_DIR, 'images'))
image_file_path = normpath(join(IMAGE_FILE_ROOT, "india_map.jpg"))


class TestUtilsText(TestCase):

    def test_get_image_size(self):
        self.assertEqual((501, 557), get_image_size(image_file_path))
