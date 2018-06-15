""" Static files in OneGov applications are served under ``/static``.

By default the ``/static`` folder of the application is used, relative to
the path of the application class. Files in that folder are available to
everyone if enabled::

    from onegov.core.framework import Framework

    class App(Framework):
        serve_static_files = True

By default, the ``/static`` path is registered, but returns 404s. This prevents
accidental serving of static files.

To change the path to be served have a look at
:meth:`onegov.core.framework.Framework.static_files`.

Note that this is not meant to serve css/javascript files, rather it's a way
to serve images, documents and other things that are really static.

Files served through this mechanism support the ``If-Modified-Since`` header.

If you need to serve something on another path you can::

    class Favicon(StaticFile):
        pass

    @App.path(model=Favicon, path='favicon.ico')
    def get_favicon(app, absorb):
        return StaticFile.from_application(app, 'favicon.ico')

"""

import os.path

from onegov.core.framework import Framework
from onegov.core.utils import render_file
from onegov.core.security import Public
from more.webassets.tweens import (
    is_subpath, has_insecure_path_element, unquote
)


class StaticFile(object):
    """ Defines a static file served by the application. """

    def __init__(self, path, version=None):
        self.path = path
        self.version = version

    @property
    def absorb(self):
        if self.version:
            return f'{self.path}___{self.version}'

        return self.path

    @classmethod
    def from_application(cls, app, absorb):
        """ Absorbs all /static/* paths and returns :class:`StaticFile`
        instances with the path set to a subpath of
        :meth:`onegov.core.Framework.static_files`.

        For security reasons this subpath is required to actually be inside the
        static_files folder. No symlinks are allowed.

        """
        if not app.serve_static_files:
            return None

        identity = unquote(absorb)
        version = None

        position = absorb.find('___')

        if position >= 0:
            identity, version = identity[:position], identity[position + 4:]

        if has_insecure_path_element(identity):
            return None

        for directory in app.static_files:
            path = os.path.join(directory, identity)

            if not is_subpath(directory, path):
                continue

            if not os.path.isfile(path):
                continue

            return cls(os.path.relpath(path, start=directory), version=version)


@Framework.path(model=StaticFile, path='/static', absorb=True)
def get_static_file(app, absorb):
    return StaticFile.from_application(app, absorb)


@Framework.view(model=StaticFile, render=render_file, permission=Public)
def view_static_file(self, request):
    """ Renders the given static file in the browser. """

    if self.version:

        @request.after
        def cache_forever(response):
            response.headers['Cache-Control'] = 'max-age=31536000'

    for directory in request.app.static_files:
        path = os.path.join(directory, self.path)

        if not os.path.isfile(path):
            continue

        assert is_subpath(directory, path)
        return path
