from pathlib import Path

from html2latex.utils.image import get_image_size

IMAGE_FILE_PATH = Path(__file__).resolve().parents[1] / "assets" / "india_map.jpg"


def test_get_image_size():
    assert get_image_size(str(IMAGE_FILE_PATH)) == (501, 557)
