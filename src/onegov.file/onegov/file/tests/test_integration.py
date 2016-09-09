import morepath
import pytest
import transaction

from depot.manager import DepotManager
from onegov.core import Framework
from onegov.core.utils import scan_morepath_modules
from onegov.file import DepotApp, FileCollection
from onegov.file.integration import SUPPORTED_STORAGE_BACKENDS
from onegov.testing.utils import create_image
from webtest import TestApp as Client


@pytest.fixture(scope='function', params=SUPPORTED_STORAGE_BACKENDS)
def app(request, postgres_dsn, temporary_path):

    backend = request.param

    class App(Framework, DepotApp):
        pass

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        depot_backend=backend,
        depot_storage_path=str(temporary_path)
    )

    app.namespace = 'apps'
    app.set_application_id('apps/my-app')

    return app


def ensure_correct_depot(app):
    # this will activate the correct depot storage - only required in these
    # tets because we are not storing the file *during* a request
    Client(app).get('/', expect_errors=True)


def test_serve_file(app):
    ensure_correct_depot(app)

    files = FileCollection(app.session())
    file_id = files.add('readme.txt', b'README').id
    transaction.commit()

    client = Client(app)
    result = client.get('/storage/{}'.format(file_id))

    assert result.body == b'README'
    assert result.content_type == 'text/plain'
    assert result.content_length == 6
    assert 'filename="readme.txt"' in result.content_disposition


def test_application_separation(app):
    app.set_application_id('apps/one')
    ensure_correct_depot(app)

    files = FileCollection(app.session())
    first_id = files.add('readme.txt', b'README').id
    transaction.commit()

    app.set_application_id('apps/two')
    ensure_correct_depot(app)

    files = FileCollection(app.session())
    second_id = files.add('readme.txt', b'README').id
    transaction.commit()

    assert len(DepotManager.get('apps-one').list()) == 1
    assert len(DepotManager.get('apps-two').list()) == 1

    client = Client(app)

    app.set_application_id('apps/one')

    assert client.get('/storage/{}'.format(first_id))\
        .status_code == 200
    assert client.get('/storage/{}'.format(second_id), expect_errors=True)\
        .status_code == 404

    app.set_application_id('apps/two')

    assert client.get('/storage/{}'.format(first_id), expect_errors=True)\
        .status_code == 404
    assert client.get('/storage/{}'.format(second_id))\
        .status_code == 200


def test_serve_thumbnail(app):
    ensure_correct_depot(app)

    files = FileCollection(app.session())
    files.add('avatar.png', create_image(1024, 1024))
    transaction.commit()

    client = Client(app)

    avatar = files.query().one()

    image = client.get('/storage/{}'.format(avatar.id))
    thumb = client.get('/storage/{}/thumbnail'.format(avatar.id))

    assert image.content_type == 'image/png'
    assert thumb.content_type == 'image/png'
    assert thumb.content_length < image.content_length

    # make sure the correct code is returned if there's no thumbnail
    files.add('readme.txt', b'README')
    transaction.commit()

    readme = files.by_filename('readme.txt').one()
    thumb = client.get(
        '/storage/{}/thumbnail'.format(readme.id), expect_errors=True)

    assert thumb.status_code == 302


def test_file_note_header(app):
    ensure_correct_depot(app)

    files = FileCollection(app.session())
    fid = files.add('avatar.png', create_image(1024, 1024), note='Avatar').id
    transaction.commit()

    client = Client(app)

    response = client.get('/storage/{}'.format(fid))
    assert response.headers['X-File-Note'] == 'Avatar'

    response = client.get('/storage/{}/thumbnail'.format(fid))
    assert response.headers['X-File-Note'] == 'Avatar'

    response = client.head('/storage/{}'.format(fid))
    assert response.headers['X-File-Note'] == 'Avatar'

    response = client.head('/storage/{}/thumbnail'.format(fid))
    assert response.headers['X-File-Note'] == 'Avatar'
