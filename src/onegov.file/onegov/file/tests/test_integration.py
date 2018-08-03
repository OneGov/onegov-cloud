import morepath
import os
import pytest
import transaction

from datetime import datetime
from depot.manager import DepotManager
from onegov.core import Framework
from onegov.core.utils import scan_morepath_modules
from onegov.file import DepotApp, FileCollection
from onegov.file.integration import SUPPORTED_STORAGE_BACKENDS
from onegov_testing.utils import create_image
from time import sleep
from webtest import TestApp as Client


@pytest.fixture(scope='function', params=SUPPORTED_STORAGE_BACKENDS)
def app(request, postgres_dsn, temporary_path, redis_url):

    with (temporary_path / 'bust').open('w') as f:
        f.write('\n'.join((
            f'#!/bin/bash',
            f'touch {temporary_path}/$1'
        )))

    os.chmod(temporary_path / 'bust', 0o775)

    backend = request.param

    class App(Framework, DepotApp):
        pass

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        depot_backend=backend,
        depot_storage_path=str(temporary_path),
        frontend_cache_buster=f'{temporary_path}/bust',
        redis_url=redis_url
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

    transaction.begin()
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

    transaction.begin()
    files = FileCollection(app.session())
    first_id = files.add('readme.txt', b'README').id
    transaction.commit()

    app.set_application_id('apps/two')
    ensure_correct_depot(app)

    transaction.begin()
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

    transaction.begin()
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

    small = client.get('/storage/{}/small'.format(avatar.id))
    assert small.content_length == thumb.content_length

    # make sure the correct code is returned if there's no thumbnail
    transaction.begin()
    files.add('readme.txt', b'README')
    transaction.commit()

    readme = files.by_filename('readme.txt').one()
    thumb = client.get(
        '/storage/{}/thumbnail'.format(readme.id), expect_errors=True)

    assert thumb.status_code == 302


def test_file_note_header(app):
    ensure_correct_depot(app)

    transaction.begin()
    files = FileCollection(app.session())
    fid = files.add('avatar.png', create_image(1024, 1024), note='Avatar').id
    transaction.commit()

    client = Client(app)

    response = client.get('/storage/{}'.format(fid))
    assert response.headers['X-File-Note'] == '{"note":"Avatar"}'

    response = client.get('/storage/{}/thumbnail'.format(fid))
    assert response.headers['X-File-Note'] == '{"note":"Avatar"}'

    response = client.head('/storage/{}'.format(fid))
    assert response.headers['X-File-Note'] == '{"note":"Avatar"}'

    response = client.head('/storage/{}/thumbnail'.format(fid))
    assert response.headers['X-File-Note'] == '{"note":"Avatar"}'


def test_bust_cache(app, temporary_path):
    ensure_correct_depot(app)

    assert not (temporary_path / 'foobar').exists()

    # ensure that this is non-blocking
    start = datetime.utcnow()
    app.bust_frontend_cache('foobar')
    assert (datetime.utcnow() - start).total_seconds() <= 1
    assert not (temporary_path / 'foobar').exists()

    # wait for it to complete
    sleep(5.1)
    assert (temporary_path / 'foobar').exists()
