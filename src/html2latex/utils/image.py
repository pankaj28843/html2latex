# Third Party Stuff
from PIL import Image


def get_image_size(path):
    """ Given the path of the image it gives the size of the image"""
    img = Image.open(path)
    return img.size
