import magic
import mimetypes
import os.path

from depot.io.utils import FileIntent
from io import IOBase


def path_from_fileobj(fileobj):
    if getattr(fileobj, 'filename', None) is not None:
        return fileobj.filename
    elif getattr(fileobj, 'name', None) is not None:
        return os.path.basename(fileobj.name)
    else:
        raise NotImplementedError


def content_type_from_fileobj(fileobj):
    """ Gets the content type from a file obj. Depot has this as well, but it
    doesn't use python-magic as a fallback, so it's less accurate, but faster.

    We however want to be as accurate as possible.

    """

    path = path_from_fileobj(fileobj)
    content_type = mimetypes.guess_type(path)

    if not content_type:
        content_type = magic.from_file(path, mime=True)
        content_type = content_type.decode('utf-8')

    return content_type


def as_fileintent(content, filename):
    assert isinstance(content, bytes) or isinstance(content, IOBase), """
        Content must be either a bytes string or a file-like object.
    """

    is_string = isinstance(content, bytes)

    if is_string:
        assert isinstance(content, bytes), "Provide content in bytes."
        return FileIntent(content, filename, 'text/plain')
    else:
        assert 'b' in content.mode, "Open file in binary mode."
        return FileIntent(
            content, filename, content_type_from_fileobj(content))
