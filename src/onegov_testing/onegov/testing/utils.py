from io import BytesIO
from PIL import Image


def create_image():
    """ Generates a test image and returns it's file handle. """

    im = BytesIO()
    image = Image.new('RGBA', size=(50, 50), color=(155, 0, 0))
    image.save(im, 'png')
    im.name = 'test.png'
    im.seek(0)
    return im
