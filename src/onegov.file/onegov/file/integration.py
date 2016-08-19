import morepath
import os.path

from depot.manager import DepotManager
from depot.middleware import FileServeApp
from more.transaction.main import transaction_tween_factory
from morepath import App
from onegov.core.security import Private, Public
from onegov.file.collection import FileCollection
from onegov.file.models import File
from pathlib import Path
from sqlalchemy.orm.attributes import flag_modified


SUPPORTED_STORAGE_BACKENDS = (
    'depot.io.local.LocalFileStorage',
    'depot.io.memory.MemoryFileStorage'
)


class DepotApp(App):
    """ Provides `Depot <depot.readthedocs.io>`_ integration for
    :class:`onegov.core.framework.Framework` based applications.

    """

    def configure_files(self, **cfg):
        """ Configures the file/depot integration. The following configuration
        options are accepted:

        :depot_backend: The depot backend to use. Supported values:

            * depot.io.local.LocalFileStorage
            * depot.io.memory.MemoryFileStorage

        :depot_storage_path: The storage path used by the local file storage.

            Note that the actual files are stored under a subdirectory specific
            to each application id. This is mainly to keep a handle on which
            file belongs to which application. Additionally it ensures that we
            aren't accidentally opening another application's files.

        """

        self.depot_backend = cfg.get('depot_backend')
        self.depot_storage_path = cfg.get('depot_storage_path')

        assert self.depot_backend in SUPPORTED_STORAGE_BACKENDS, """
            A depot app *must* have a valid storage backend set up.
        """

        if self.depot_backend == 'depot.io.local.LocalFileStorage':
            assert os.path.isdir(self.depot_storage_path), """
                The depot storage path must exist.
            """

    @property
    def bound_depot_id(self):
        return self.schema

    @property
    def bound_depot(self):
        assert DepotManager._default_depot == self.bound_depot_id
        return DepotManager.get()

    @property
    def bound_storage_path(self):
        return Path(self.depot_storage_path) / self.schema

    def create_depot(self):
        config = {
            'depot.backend': self.depot_backend
        }

        if self.depot_backend.endswith('LocalFileStorage'):
            path = self.bound_storage_path

            if not path.exists():
                path.mkdir()

            config['depot.storage_path'] = str(path)

        elif self.depot_backend.endswith('MemoryFileStorage'):
            pass

        else:
            # implementing non-local file systems is going to be more
            # invloved, because we do not generate external urls yet
            raise NotImplementedError()

        DepotManager.configure(self.bound_depot_id, config)

    def bind_depot(self):
        if self.bound_depot_id not in DepotManager._depots:
            self.create_depot()

        DepotManager.set_default(self.schema)


@DepotApp.tween_factory(over=transaction_tween_factory)
def configure_depot_tween_factory(app, handler):

    assert app.has_database_connection, "This module requires a db backed app."

    def configure_depot_tween(request):
        app.bind_depot()
        return handler(request)

    return configure_depot_tween


def render_depot_file(file, request):
    return request.get_response(
        FileServeApp(file, cache_max_age=3600 * 24 * 7))


def respond_with_alt_text(reference, request):
    @request.after
    def include_alt_text(response):
        response.headers.add('X-File-Note', reference.note or '')


@DepotApp.path(model=File, path='/storage/{id}')
def get_file(app, id):
    return FileCollection(app.session()).by_id(id)


@DepotApp.view(model=File, render=render_depot_file, permission=Public)
def view_file(self, request):
    respond_with_alt_text(self, request)
    return self.reference.file


@DepotApp.view(model=File, name='thumbnail', render=render_depot_file,
               permission=Public)
def view_thumbnail(self, request):
    respond_with_alt_text(self, request)

    # we currently only have one thumbnail, in the future we might make this
    # a query parameter:
    thumbnail_id = self.get_thumbnail_id(size='small')

    if not thumbnail_id:
        return morepath.redirect(request.link(self))

    return request.app.bound_depot.get(thumbnail_id)


@DepotApp.view(model=File, render=render_depot_file, permission=Public,
               request_method='HEAD')
def view_file_head(self, request):

    @request.after
    def set_cache(response):
        response.cache_control.max_age = 60

    return view_file(self, request)


@DepotApp.view(model=File, name='thumbnail', render=render_depot_file,
               permission=Public, request_method='HEAD')
def view_thumbnail_head(self, request):

    @request.after
    def set_cache(response):
        response.cache_control.max_age = 60

    return view_thumbnail(self, request)


@DepotApp.view(model=File, name='note', request_method='POST',
               permission=Private)
def handle_note_update(self, request):
    request.assert_valid_csrf_token()
    self.note = request.POST.get('note')

    # when updating the alt text we offer the option not to update the
    # modified date, which is helpful if the files are in modified order
    # and the order should remain when the note is changed
    if request.POST.get('keep-timestamp') in ('1', 'true', 'yes'):
        self.modified = self.modified
        flag_modified(self, 'modified')


@DepotApp.view(model=File, request_method='DELETE', permission=Private)
def delete_file(self, request):
    """ Deletes the given file. By default the permission is
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
    FileCollection(request.app.session()).delete(self)
