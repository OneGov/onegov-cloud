import magic

from contextlib import suppress
from depot.io.utils import FileIntent
from io import IOBase, BytesIO, UnsupportedOperation
from lxml import etree
from PIL import Image


def content_type_from_fileobj(fileobj):
    """ Gets the content type from a file obj. Depot has this as well, but it
    doesn't use python-magic. We use python-magic to be slower, but more
    accurate.

    """

    with suppress(UnsupportedOperation):
        fileobj.seek(0)

    return magic.from_buffer(fileobj.read(4096), mime=True)


def as_fileintent(content, filename):
    assert isinstance(content, bytes) or isinstance(content, IOBase), """
        Content must be either a bytes string or a file-like object.
    """

    if isinstance(content, bytes):
        return FileIntent(BytesIO(content), filename, 'text/plain')
    else:
        if hasattr(content, 'mode'):
            assert 'b' in content.mode, "Open file in binary mode."

        if hasattr(content, 'seek'):
            content.seek(0)

        return FileIntent(
            content, filename, content_type_from_fileobj(content))


def get_supported_image_mime_types():
    """ Queries PIL for *all* locally supported mime types.

    Adapted from:
    https://github.com/python-pillow/Pillow/issues/1182#issuecomment-90572583

    """

    # Make sure all supported formats are registered.
    Image.init()

    # Not all PIL formats register a mime type, fill in the blanks ourselves.
    supported_types = {
        'image/bmp',
        'image/x-bmp',
        'image/x-MS-bmp',
        'image/x-icon',
        'image/x-ico',
        'image/x-win-bitmap',
        'image/x-pcx',
        'image/x-portable-pixmap',
        'image/x-tga'
    }

    for mime in Image.MIME.values():

        # exclude pdfs, postscripts and the like
        if not mime.startswith('application/'):
            supported_types.add(mime)

    return supported_types


def get_svg_size(svg):
    # note, the svg size may not be in pixel, it can include the same units
    # the browser uses for styling, so we need to pass this information down
    # to the browser, instead of using it internally
    root = etree.parse(svg).getroot()
    return root.get('width'), root.get('height')


def get_image_size(image):
    return tuple('{}px'.format(d) for d in image.size)


# we don't support *all* the image types PIL supports
EXCLUDED_IMAGE_TYPES = {'application/pdf'}
IMAGE_MIME_TYPES = get_supported_image_mime_types() - EXCLUDED_IMAGE_TYPES
IMAGE_MIME_TYPES_AND_SVG = IMAGE_MIME_TYPES | {'image/svg+xml'}
