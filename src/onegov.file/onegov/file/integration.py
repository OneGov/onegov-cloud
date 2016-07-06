import os.path

from depot.manager import DepotManager
from depot.middleware import FileServeApp
from more.transaction.main import transaction_tween_factory
from morepath import App
from onegov.core.security import Public
from onegov.file.collection import FileCollection
from onegov.file.models import File
from pathlib import Path


SUPPORTED_STORAGE_BACKENDS = (
    'depot.io.local.LocalFileStorage',
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
    def bound_storage_depot(self):
        return self.schema

    @property
    def bound_storage_path(self):
        return Path(self.depot_storage_path) / self.schema


@DepotApp.tween_factory(over=transaction_tween_factory)
def configure_depot_tween_factory(app, handler):

    assert app.has_database_connection, "This module requires a db backed app."

    def configure_depot_tween(request):
        if app.bound_storage_depot not in DepotManager._depots:
            path = app.bound_storage_path

            if not path.exists():
                path.mkdir()

            DepotManager.configure(app.bound_storage_depot, {
                'depot.backend': app.depot_backend,
                'depot.storage_path': str(path)
            })

        DepotManager.set_default(app.schema)

        return handler(request)

    return configure_depot_tween


@DepotApp.path(model=File, path='/storage/{file_id}')
def get_file(app, file_id):
    return FileCollection(app.session()).by_id(file_id)


@DepotApp.view(model=File, permission=Public)
def view_file(self, request):
    return request.get_response(
        FileServeApp(self.reference.file, cache_max_age=3600 * 24 * 7))
