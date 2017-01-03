import magic
import mimetypes
import os.path

from depot.io.utils import FileIntent
from io import IOBase, BytesIO
from lxml import etree
from PIL import Image


def path_from_fileobj(fileobj):
    if getattr(fileobj, 'filename', None) is not None:
        return fileobj.filename
    elif getattr(fileobj, 'name', None) is not None:
        if isinstance(fileobj.name, str):
            return os.path.basename(fileobj.name)


def content_type_from_fileobj(fileobj):
    """ Gets the content type from a file obj. Depot has this as well, but it
    doesn't use python-magic as a fallback, so it's less accurate, but faster.

    We however want to be as accurate as possible.

    """

    path = path_from_fileobj(fileobj)
    content_type = path and mimetypes.guess_type(path)[0] or None

    if not content_type:

        if path:
            content_type = magic.from_file(path, mime=True)
        else:
            content_type = magic.from_buffer(fileobj.read(1024), mime=True)

        fileobj.seek(0)

    return content_type


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
