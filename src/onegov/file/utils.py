from __future__ import annotations

import hashlib
import magic
import os

from contextlib import contextmanager, suppress
from depot.io.utils import FileIntent
from functools import lru_cache
from mimetypes import guess_extension
from io import IOBase, BytesIO, UnsupportedOperation
from lxml import etree
from PIL import Image


from typing import IO, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRead, StrOrBytesPath
    from collections.abc import Iterator


def content_type_from_fileobj(fileobj: SupportsRead[bytes]) -> str:
    """ Gets the content type from a file obj. Depot has this as well, but it
    doesn't use python-magic. We use python-magic to be slower, but more
    accurate.

    """

    if hasattr(fileobj, 'seek'):
        with suppress(UnsupportedOperation):
            fileobj.seek(0)

    return magic.from_buffer(fileobj.read(4096), mime=True)


def as_fileintent(
    content: bytes | IO[bytes],
    filename: str | None
) -> FileIntent:

    # this is far stricter than filedepot is, but our custom UploadedFile
    # requires more than just a read() to be implemented, this check won't
    # make mypy happy, since IOBase does not inherit from typing.IO
    # the minimum we could get away with right now is SupportsReadCloseSeek
    # which is not that far off what IO provides, so for simplicity let's
    # just use that
    msg = 'Content must be either a bytes string or a file-like object.'
    assert isinstance(content, (bytes, IOBase)), msg

    if isinstance(content, bytes):
        return FileIntent(BytesIO(content), filename, 'text/plain')
    else:
        if hasattr(content, 'mode'):  # type: ignore[unreachable]
            assert 'b' in content.mode, 'Open file in binary mode.'

        if hasattr(content, 'seek'):
            content.seek(0)

        return FileIntent(
            content, filename, content_type_from_fileobj(content))


@lru_cache(maxsize=1)
def get_supported_image_mime_types() -> set[str]:
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


# TODO: technically SupportsReadClose is enough
def get_svg_size(svg: IO[bytes]) -> tuple[str | None, str | None]:
    # note, the svg size may not be in pixel, it can include the same units
    # the browser uses for styling, so we need to pass this information down
    # to the browser, instead of using it internally
    root = etree.parse(svg).getroot()
    return root.get('width'), root.get('height')


def extension_for_content_type(
    content_type: str,
    filename: str | None = None
) -> str:
    """ Gets the extension for the given content type. Note that this is
    *meant for display only*. A file claiming to be a PDF might not be one,
    but this function would not let you know that.

    """

    if filename is not None:
        # previously we checked if the extension was at most 3 characters
        # while I understand the motivation behind this, I don't think it
        # is a good idea to make long file extensions not work, just to
        # support files without an extension that have a `.` in the name
        _, sep, ext = filename.rpartition('.')
        ext = ext.lower() if sep else ''
    else:
        ext = guess_extension(content_type, strict=False) or ''

    return ext.strip('. ')


def get_image_size(image: Image.Image) -> tuple[str, str]:
    w, h = image.size
    return f'{w}px', f'{h}px'


def digest(
    fileobj: SupportsRead[bytes],
    type: str = 'sha256',
    chunksize: int = 4096
) -> str:

    if hasattr(fileobj, 'seek'):
        with suppress(UnsupportedOperation):
            fileobj.seek(0)

    digest = getattr(hashlib, type)()

    for chunk in iter(lambda: fileobj.read(chunksize), b''):
        digest.update(chunk)

    return digest.hexdigest()


def word_count(text: str) -> int:
    """ The word-count of the given text. Goes through the string exactly
    once and has constant memory usage. Not super sophisticated though.

    """
    if not text:
        return 0

    count = 0
    inside_word = False

    for char in text:
        if char.isspace():
            inside_word = False
        elif not inside_word:
            count += 1
            inside_word = True

    return count


def name_without_extension(name: str) -> str:
    # previously we checked if the extension was at most 3 characters
    # while I understand the motivation behind this, I don't think it
    # is a good idea to make long file extensions not work, just to
    # support files without an extension that have a `.` in the name
    name, sep, ext = name.rpartition('.')
    # if there is no sep, then the original string will be in ext
    return name if sep else ext


@contextmanager
def current_dir(dir: StrOrBytesPath) -> Iterator[None]:
    previous = os.getcwd()
    os.chdir(dir)
    yield
    os.chdir(previous)


# we don't support *all* the image types PIL supports
EXCLUDED_IMAGE_TYPES = {'application/pdf'}
IMAGE_MIME_TYPES = get_supported_image_mime_types() - EXCLUDED_IMAGE_TYPES
IMAGE_MIME_TYPES_AND_SVG = IMAGE_MIME_TYPES | {'image/svg+xml'}
