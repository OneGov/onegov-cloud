""" Filestorage is a way to store files locally or on a remote server, with the
interface being the same, no matter where the files are stored.

Based on `<https://docs.pyfilesystem.org/en/latest/>`_

See :attr:`onegov.core.framework.Framework.filestorage` for more information.

"""
from __future__ import annotations

import os
import os.path
import re
import shutil

from datetime import datetime, UTC
from onegov.core.framework import Framework
from onegov.core.crypto import random_token
from onegov.core.utils import render_file
from onegov.core.security import Public, Private
from time import time
from threading import RLock


from typing import overload, Any, IO, Literal, Self, TYPE_CHECKING
if TYPE_CHECKING:
    import io
    from _typeshed import (
        OpenBinaryMode,
        OpenBinaryModeReading,
        OpenBinaryModeUpdating,
        OpenBinaryModeWriting,
        OpenTextMode,
        StrOrBytesPath
    )
    from .request import CoreRequest


def random_filename() -> str:
    """ Returns a random filename that can't be guessed. """
    return random_token()


class IllegalBackReference(ValueError):
    """ Too many backrefs exist in a path. """
    def __init__(self, path: str) -> None:
        super().__init__(
            f'path {path!r} contains back-references outside of filesystem'
        )


_requires_normalization = re.compile(r'(^|/)\.\.?($|/)|//').search


def normpath(path: str) -> str:
    if path == '' or path == '/':
        return path

    if not _requires_normalization(path):
        return path.rstrip('/')

    components: list[str] = []
    for component in path.split('/'):
        if component == '..':
            if not components:
                raise IllegalBackReference(path)
            components.pop()
        elif component == '.' or component == '':
            pass
        else:
            components.append(component)
    normalized = '/'.join(components)
    return '/' + normalized if path.startswith('/') else normalized


class Filestorage:
    """ A minimal implementation of ``fs``/``PyFilesystem``'s ``OSFS``
    class, that can do everything we need in OneGov.

    Since ``fs`` was no longer maintained and the maintained alternative
    ``fsspec`` does not yet have type hints of any kind and we don't
    really use anything other than ``OSFS`` in any of our deployments
    this seemed like the most sensible solution.

    We can always migrate to ``fsspec`` later, if we do end up needing
    more control again.
    """

    def __init__(
        self,
        root_path: StrOrBytesPath,
        create: bool = False,
        create_mode: int = 0o777,
        expand_vars: bool = True,
    ) -> None:
        self._lock = RLock()
        self.root_path = root_path = os.fsdecode(root_path)
        _root_path = root_path or '/'
        if expand_vars:
            _root_path = os.path.expandvars(_root_path)
        self._root_path = os.path.normpath(
            os.path.abspath(os.path.expanduser(_root_path))
        )
        if create:
            os.makedirs(_root_path, mode=create_mode, exist_ok=True)
        else:
            if not os.path.isdir(_root_path):
                raise RuntimeError('Missing filestorage root directory')

    def hassyspath(self, path: str) -> bool:
        return True

    def validatepath(self, path: str) -> str:
        if '\0' in path:
            raise ValueError('Invalid path')

        # TODO: Do we want to validate max path length?
        return '/' + normpath(path).lstrip('/')

    def getsyspath(self, path: str) -> str:
        return os.path.join(
            self._root_path,
            self.validatepath(path).lstrip('/').replace('/', os.sep)
        )

    def hasurl(self, path: str) -> bool:
        return True

    def geturl(self, path: str) -> str:
        return 'file://' + self.getsyspath(path)

    def exists(self, path: str) -> bool:
        return os.path.exists(self.getsyspath(path))

    def isdir(self, path: str) -> bool:
        return os.path.isdir(self.getsyspath(path))

    def isfile(self, path: str) -> bool:
        return os.path.isfile(self.getsyspath(path))

    def opendir(self, path: str) -> Self:
        subfs = type(self)(self.getsyspath(path))
        # de-normalize the displayed root path
        # but ensure we don't drop a required separator
        subfs.root_path.replace(
            self._root_path,
            self.root_path if self.root_path.endswith(os.sep)
            else self.root_path + os.sep
        )
        return subfs

    def makedir(self, path: str, recreate: bool = False) -> Self:
        sys_path = self.getsyspath(path)
        if not (recreate and os.path.isdir(sys_path)):
            os.mkdir(sys_path)
        return self.opendir(path)

    def listdir(self, path: str) -> list[str]:
        return [
            os.fsdecode(name)
            for name in os.listdir(os.fsencode(self.getsyspath(path)))
        ]

    def create(self, path: str) -> bool:
        with self._lock:
            sys_path = self.getsyspath(path)
            if os.path.exists(sys_path):
                return False

            with open(sys_path, mode='wb'):
                return True

    def touch(self, path: str) -> None:
        with self._lock:
            now = time()
            if not self.create(path):
                os.utime(self.getsyspath(path), (now, now))

    def remove(self, path: str) -> None:
        os.remove(self.getsyspath(path))

    def removetree(self, path: str) -> None:
        with self._lock:
            sys_path = self.getsyspath(path)
            if sys_path.rstrip('/') != self._root_path:
                # simple case, since we don't need to preserve the root
                shutil.rmtree(self.getsyspath(path))
                return

            with os.scandir(sys_path) as dir_iter:
                for entry in dir_iter:
                    if entry.is_dir(follow_symlinks=False):
                        shutil.rmtree(entry.path)
                    else:
                        os.remove(entry.path)

    @overload
    def open(
        self,
        path: str,
        mode: OpenTextMode = 'r',
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str = '',
    ) -> io.TextIOWrapper: ...
    @overload
    def open(
        self,
        path: str,
        mode: OpenBinaryMode,
        buffering: Literal[0],
        encoding: None = None,
        errors: None = None,
        newline: str = '',
    ) -> io.FileIO: ...
    @overload
    def open(
        self,
        path: str,
        mode: OpenBinaryModeUpdating,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: str = '',
    ) -> io.BufferedRandom: ...
    @overload
    def open(
        self,
        path: str,
        mode: OpenBinaryModeWriting,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: str = '',
    ) -> io.BufferedWriter: ...
    @overload
    def open(
        self,
        path: str,
        mode: OpenBinaryModeReading,
        buffering: Literal[-1, 1] = -1,
        encoding: None = None,
        errors: None = None,
        newline: str = '',
    ) -> io.BufferedReader: ...
    @overload
    def open(
        self,
        path: str,
        mode: OpenBinaryMode,
        buffering: int = -1,
        encoding: None = None,
        errors: None = None,
        newline: str = '',
    ) -> IO[bytes]: ...
    @overload
    def open(
        self,
        path: str,
        mode: str,
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str = '',
    ) -> IO[Any]: ...

    def open(
        self,
        path: str,
        mode: str = 'r',
        buffering: int = -1,
        encoding: str | None = None,
        errors: str | None = None,
        newline: str = '',
    ) -> IO[Any]:

        is_binary = 'b' in mode
        return open(
            self.getsyspath(path),
            mode=mode,
            buffering=buffering,
            encoding=None if is_binary else (encoding or 'utf-8'),
            errors=errors,
            newline=None if is_binary else newline,
        )

    def writebytes(self, path: str, contents: bytes) -> None:
        with self.open(path, 'wb') as fp:
            fp.write(contents)

    def readbytes(self, path: str) -> bytes:
        with self.open(path, 'rb') as fp:
            return fp.read()

    def writetext(self, path: str, contents: str) -> None:
        with self.open(path, 'wt') as fp:
            fp.write(contents)

    def readtext(self, path: str) -> str:
        with self.open(path, 'rt') as fp:
            return fp.read()

    # NOTE: This is not part of the FS interface, but modified is the
    #       only info we ever access in our code, so we just added a
    #       helper for that instead of implenting the whole info thing
    def getmodified(self, path: str) -> datetime:
        stat = os.stat(self.getsyspath(path))
        return datetime.fromtimestamp(stat.st_mtime, UTC)

    def __repr__(self) -> str:
        return f'Filestorage({self.root_path!r})'

    def __str__(self) -> str:
        return f"<Filestorage '{self.root_path}'>"


class FilestorageFile:
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

    def __init__(self, path: str):
        self.path = path

    @property
    def absorb(self) -> str:
        return self.path


@Framework.path(model=FilestorageFile, path='/files', absorb=True)
def get_filestorage_file(
    app: Framework,
    absorb: str
) -> FilestorageFile | None:
    try:
        assert app.filestorage is not None
        if app.filestorage.isfile(absorb):
            return FilestorageFile(absorb)
    except IllegalBackReference:
        pass
    return None


@Framework.view(model=FilestorageFile, render=render_file, permission=Public)
def view_filestorage_file(
    self: FilestorageFile,
    request: CoreRequest
) -> str:
    """ Renders the given filestorage file in the browser. """
    return getattr(request.app, self.storage).getsyspath(self.path)


@Framework.view(
    model=FilestorageFile, request_method='DELETE', permission=Private)
def delete_static_file(self: FilestorageFile, request: CoreRequest) -> None:
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
    assert request.app.filestorage is not None
    request.app.filestorage.remove(self.path)
