from __future__ import unicode_literals

from unittest import TestCase
import os.path
import html2latex.utils.image as imag

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_FILE_ROOT = os.path.normpath(os.path.join(CURRENT_DIR, 'images'))
image_file_path = os.path.normpath(
    os.path.join(IMAGE_FILE_ROOT, "india_map.jpg"))


class TestUtilsText(TestCase):

    def test_get_image_size(self):
        self.assertEqual(
            (501, 557), imag.get_image_size(image_file_path))
