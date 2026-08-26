from __future__ import annotations

import morepath
import os.path
import pytest

from onegov.core.framework import Framework
from onegov.core import utils
from onegov.core.filestorage import Filestorage, IllegalBackReference
from webtest import TestApp as Client


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from webob import Response


def test_validatepath(temporary_directory: str) -> None:
    filestorage = Filestorage(temporary_directory)

    with pytest.raises(ValueError, match=r'Invalid path'):
        filestorage.validatepath('\0null_byte.txt')

    with pytest.raises(IllegalBackReference):
        filestorage.validatepath('../cannot_escape')

    assert filestorage.validatepath(
        'but/can/../../mess/../around'
    ) == '/around'

    assert filestorage.validatepath('.') == '/'


def test_create(temporary_directory: str) -> None:
    filestorage = Filestorage(temporary_directory)
    assert filestorage.create('foo')
    modified = filestorage.getmodified('foo')
    assert not filestorage.create('foo')
    assert filestorage.getmodified('foo') == modified


def test_touch(temporary_directory: str) -> None:
    filestorage = Filestorage(temporary_directory)
    assert not filestorage.exists('foo')
    filestorage.touch('foo')
    assert filestorage.exists('foo')
    modified = filestorage.getmodified('foo')
    filestorage.touch('foo')
    assert filestorage.getmodified('foo') > modified


def test_repr_and_str(temporary_directory: str) -> None:
    filestorage = Filestorage(temporary_directory)
    assert repr(temporary_directory) in repr(filestorage)
    assert temporary_directory in str(filestorage)
    assert str(filestorage) != repr(filestorage)


def test_removetree(temporary_directory: str) -> None:
    filestorage = Filestorage(temporary_directory)
    foo = filestorage.makedir('foo')
    bar = filestorage.makedir('bar')
    baz = foo.makedir('baz')
    filestorage.writetext('root.txt', 'root')
    foo.writetext('foo.txt', 'foo')
    bar.writetext('bar.txt', 'bar')
    baz.writetext('baz.txt', 'baz')

    assert set(filestorage.listdir('.')) == {'root.txt', 'foo', 'bar'}
    assert set(filestorage.listdir('foo')) == {'foo.txt', 'baz'}
    assert set(filestorage.listdir('bar')) == {'bar.txt'}
    assert set(filestorage.listdir('foo/baz')) == {'baz.txt'}

    filestorage.removetree('bar')
    assert not filestorage.exists('bar')
    assert set(filestorage.listdir('.')) == {'root.txt', 'foo'}
    assert set(filestorage.listdir('foo')) == {'foo.txt', 'baz'}
    assert set(filestorage.listdir('foo/baz')) == {'baz.txt'}

    filestorage.removetree('.')
    assert not filestorage.listdir('.')
    assert not filestorage.exists('foo')
    assert not filestorage.exists('bar')
    assert not filestorage.exists('root.txt')


def test_independence(temporary_directory: str) -> None:

    class App(Framework):
        pass

    app = App()
    app.namespace = 'tests'
    app.configure_application(
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory
        }
    )

    app.set_application_id('tests/foo')
    assert app.filestorage is not None
    app.filestorage.writetext('document.txt', 'foo')
    assert app.filestorage.readbytes('document.txt') == b'foo'
    assert app.filestorage.readtext('document.txt') == 'foo'

    app.set_application_id('tests/bar')
    assert not app.filestorage.exists('document.txt')
    app.filestorage.writetext('document.txt', 'bar')
    assert app.filestorage.readbytes('document.txt') == b'bar'
    assert app.filestorage.readtext('document.txt') == 'bar'

    app.set_application_id('tests/foo')
    assert app.filestorage.readbytes('document.txt') == b'foo'
    assert app.filestorage.readtext('document.txt') == 'foo'

    assert os.path.isdir(os.path.join(temporary_directory, 'tests-foo'))
    assert os.path.isdir(os.path.join(temporary_directory, 'tests-bar'))
    assert os.path.isfile(
        os.path.join(temporary_directory, 'tests-foo/document.txt'))
    assert os.path.isfile(
        os.path.join(temporary_directory, 'tests-bar/document.txt'))


def test_filestorage(temporary_directory: str, redis_url: str) -> None:

    class App(Framework):
        pass

    @App.path('/')
    class Model:
        pass

    @App.path('/login')
    class Login:
        pass

    @App.view(model=Model)
    def view_file(self: Model, request: CoreRequest) -> str | None:
        return request.filestorage_link(request.GET['file'])

    @App.view(model=Login)
    def view_login(self: Login, request: CoreRequest) -> None:

        @request.after
        def remember_login(response: Response) -> None:
            request.app.remember_identity(response, request, morepath.Identity(
                userid=request.GET['userid'],
                uid='1',
                groupids=frozenset({'admins'}),
                role='admin',
                application_id=request.app.application_id,
            ))

    @App.view(model=Model, name='csrf-token')
    def view_csrf_token(self: Model, request: CoreRequest) -> bytes:
        return request.new_csrf_token()

    utils.scan_morepath_modules(App)
    App.commit()

    app = App()
    app.namespace = 'tests'
    app.configure_application(
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory
        },
        identity_secure=False,
        redis_url=redis_url
    )
    app.set_application_id('tests/foo')
    assert app.filestorage is not None
    app.filestorage.writetext('test.txt', 'asdf')
    app.filestorage.writetext('readme', 'readme')

    client = Client(app)
    assert client.get('/?file=test.txt').text\
        == 'http://localhost/files/test.txt'
    assert client.get('/?file=asdf.txt').text == ''

    assert client.get('/files/test.txt').text == 'asdf'
    assert client.get('/files/test.txt').content_type == 'text/plain'

    assert client.get('/files/readme').text == 'readme'
    assert client.get('/files/readme').content_type == 'text/plain'

    app.set_application_id('tests/bar')

    client = Client(app)
    assert client.get('/?file=test.txt').text == ''
    assert client.get('/?file=asdf.txt').text == ''

    assert client.get('/files/test.txt', expect_errors=True).status_code == 404

    # we can't access files from the other schema via backreferences
    assert client.get(
        '/files/../foo/test.txt',
        expect_errors=True
    ).status_code == 404

    app.set_application_id('tests/foo')
    assert client.get('/files/readme').status_code == 200
    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 403

    anonymous_client = Client(app)
    anonymous_csrf_token = anonymous_client.get('/csrf-token').text.strip()

    client.get('/login?userid=test')
    logged_in_csrf_token = client.get('/csrf-token').text.strip()

    admin_client = Client(app)
    admin_client.get('/login?userid=admin')
    admin_csrf_token = admin_client.get('/csrf-token').text.strip()

    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 403

    # NOTE: Even though this CSRF Token was generated by an anonymous user
    #       because it's a different session from our logged in user the
    #       CSRF Token will be rejected
    protected_url = '/files/readme?csrf-token={}'.format(anonymous_csrf_token)
    assert client.delete(protected_url, expect_errors=True).status_code == 403

    protected_url = '/files/readme?csrf-token={}'.format(admin_csrf_token)
    assert client.delete(protected_url, expect_errors=True).status_code == 403

    protected_url = '/files/readme?csrf-token={}'.format(logged_in_csrf_token)
    assert client.delete(protected_url).status_code == 200

    assert client.get('/files/readme', expect_errors=True).status_code == 404
    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 404
