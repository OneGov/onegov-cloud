import morepath
import transaction

from onegov.core import Framework
from onegov.core.utils import scan_morepath_modules
from onegov.file import DepotApp, FileCollection
from webtest import TestApp as Client


def test_serve_file(postgres_dsn, temporary_path):

    class App(Framework, DepotApp):
        pass

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        depot_backend='depot.io.local.LocalFileStorage',
        depot_storage_path=str(temporary_path)
    )

    app.namespace = 'apps'
    app.set_application_id('apps/my-app')

    client = Client(app)

    # this will activate the correct depot storage - only required in these
    # tets because we are not storing the file *during* a request
    client.get('/', expect_errors=True)

    files = FileCollection(app.session())
    file_id = files.add('readme.txt', b'README').id
    transaction.commit()

    client = Client(app)
    result = client.get('/storage/{}'.format(file_id))

    assert result.body == b'README'
    assert result.content_type == 'text/plain'
    assert result.content_length == 6
    assert 'filename=readme.txt' in result.content_disposition
