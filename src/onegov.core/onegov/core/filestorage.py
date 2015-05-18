""" Filestorage is a way to store files locally or on a remote server, with the
interface being the same, no matter where the files are stored.

Based on `<http://docs.pyfilesystem.org/en/latest/>`_

See :attr:`onegov.core.framework.Framework.filestorage` for more information.

"""

from fs.errors import BackReferenceError
from onegov.core import Framework
from onegov.core.crypto import random_token
from onegov.core.utils import render_file
from onegov.core.security import Public, Private


def random_filename():
    """ Returns a random filename that can't be guessed. """
    return random_token()


class FilestorageFile(object):
    """ Defines a static file served by the application. The difference
    between this and :class:`onegov.core.static.StaticFile` is the storage.

    Filestorage files are stored per application_id locally or on the cloud.
    Static files are the same for the whole application class and they are
    deployed statically. That means they are not content, but part of
    the distribution.

    Note that this is only used if the file is local. Files stored in the
    filestorage should be linked using
    :meth:`onegov.core.request.CoreRequest.filestorage_link`, which might
    result in a local path, for which this class is used. Or it might result in
    a remote path that is served by some different webserver.

    """
    storage = 'filestorage'

    def __init__(self, path):
        self.path = path

    @property
    def absorb(self):
        return self.path


@Framework.path(model=FilestorageFile, path='/files', absorb=True)
def get_filestorage_file(app, absorb):
    try:
        if app.filestorage.exists(absorb):
            return FilestorageFile(absorb)
    except BackReferenceError:
        return None


@Framework.view(model=FilestorageFile, render=render_file, permission=Public)
def view_filestorage_file(self, request):
    """ Renders the given filestorage file in the browser. """
    return getattr(request.app, self.storage).getsyspath(self.path)


@Framework.view(
    model=FilestorageFile, request_method='DELETE', permission=Private)
def delete_static_file(self, request):
    """ Deletes the given filestorage file. By default the permission is
    ``Private``. An application using the framework can override this though.

    Since a DELETE can only be sent through AJAX it is protected by the
    same-origin policy. That means that we don't need to use any CSRF
    protection here.

    That being said, browser bugs and future changes in the HTML standard
    make it possible for this to happen one day. Therefore, a time-limited
    token must be passed as query parameter to this function.

    New tokens can be acquired through ``request.new_csrf_token``.

    """
    request.assert_valid_csrf_token()
    request.app.filestorage.remove(self.path)
