import more.webassets
import morepath
import onegov.core
import os.path

from morepath import setup
from onegov.core import Framework
from webtest import TestApp as Client


def test_independence(temporary_directory):

    class App(Framework):
        pass

    app = App()
    app.configure_application(
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory
        }
    )
    app.namespace = 'tests'

    app.set_application_id('tests/foo')
    app.filestorage.setcontents('document.txt', 'foo')
    assert app.filestorage.getcontents('document.txt') == b'foo'

    app.set_application_id('tests/bar')
    assert not app.filestorage.exists('document.txt')
    app.filestorage.setcontents('document.txt', 'bar')
    assert app.filestorage.getcontents('document.txt') == b'bar'

    app.set_application_id('tests/foo')
    assert app.filestorage.getcontents('document.txt') == b'foo'

    assert os.path.isdir(os.path.join(temporary_directory, 'tests-foo'))
    assert os.path.isdir(os.path.join(temporary_directory, 'tests-bar'))
    assert os.path.isfile(
        os.path.join(temporary_directory, 'tests-foo/document.txt'))
    assert os.path.isfile(
        os.path.join(temporary_directory, 'tests-bar/document.txt'))


def test_filestorage(temporary_directory):

    config = setup()

    class App(Framework):
        testing_config = config

    @App.path('/')
    class Model(object):
        pass

    @App.path('/login')
    class Login(object):
        pass

    @App.view(model=Model)
    def view_file(self, request):
        return request.filestorage_link(request.params.get('file'))

    @App.view(model=Login)
    def view_login(self, request):

        @request.after
        def remember_login(response):
            morepath.remember_identity(response, request, morepath.Identity(
                userid='test',
                role='admin',
                application_id=request.app.application_id
            ))

    @App.view(model=Model, name='csrf-token')
    def view_csrf_token(self, request):
        return request.new_csrf_token()

    config.scan(onegov.core)
    config.scan(more.webassets)
    config.commit()

    app = App()
    app.configure_application(
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory
        },
        identity_secure=False
    )
    app.namespace = 'tests'
    app.set_application_id('tests/foo')
    app.filestorage.setcontents('test.txt', 'asdf')
    app.filestorage.setcontents('readme', 'readme')

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

    app.set_application_id('tests/foo')
    assert client.get('/files/readme').status_code == 200
    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 403

    anonymous_csrf_token = client.get('/csrf-token').text.strip()
    client.get('/login')
    logged_in_csrf_token = client.get('/csrf-token').text.strip()

    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 403

    protected_url = '/files/readme?csrf-token={}'.format(anonymous_csrf_token)
    assert client.delete(protected_url, expect_errors=True).status_code == 403

    protected_url = '/files/readme?csrf-token={}'.format(logged_in_csrf_token)
    assert client.delete(protected_url, expect_errors=True).status_code == 200

    assert client.get('/files/readme', expect_errors=True).status_code == 404
    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 404
