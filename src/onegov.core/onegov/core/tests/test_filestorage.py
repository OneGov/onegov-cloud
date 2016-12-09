import morepath
import os.path

from onegov.core.framework import Framework
from onegov.core import utils
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
    app.filestorage.settext('document.txt', 'foo')
    assert app.filestorage.getbytes('document.txt') == b'foo'
    assert app.filestorage.gettext('document.txt') == 'foo'

    app.set_application_id('tests/bar')
    assert not app.filestorage.exists('document.txt')
    app.filestorage.settext('document.txt', 'bar')
    assert app.filestorage.getbytes('document.txt') == b'bar'
    assert app.filestorage.gettext('document.txt') == 'bar'

    app.set_application_id('tests/foo')
    assert app.filestorage.getbytes('document.txt') == b'foo'
    assert app.filestorage.gettext('document.txt') == 'foo'

    assert os.path.isdir(os.path.join(temporary_directory, 'tests-foo'))
    assert os.path.isdir(os.path.join(temporary_directory, 'tests-bar'))
    assert os.path.isfile(
        os.path.join(temporary_directory, 'tests-foo/document.txt'))
    assert os.path.isfile(
        os.path.join(temporary_directory, 'tests-bar/document.txt'))


def test_filestorage(temporary_directory):

    class App(Framework):
        pass

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
            request.app.remember_identity(response, request, morepath.Identity(
                userid=request.params.get('userid'),
                role='admin',
                application_id=request.app.application_id
            ))

    @App.view(model=Model, name='csrf-token')
    def view_csrf_token(self, request):
        return request.new_csrf_token()

    utils.scan_morepath_modules(App)
    App.commit()

    app = App()
    app.configure_application(
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': temporary_directory
        },
        identity_secure=False,
        disable_memcached=True
    )
    app.namespace = 'tests'
    app.set_application_id('tests/foo')
    app.filestorage.settext('test.txt', 'asdf')
    app.filestorage.settext('readme', 'readme')

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
    client.get('/login?userid=test')
    logged_in_csrf_token = client.get('/csrf-token').text.strip()

    admin_client = Client(app)
    admin_client.get('/login?userid=admin')
    admin_csrf_token = admin_client.get('/csrf-token').text.strip()

    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 403

    protected_url = '/files/readme?csrf-token={}'.format(anonymous_csrf_token)
    assert client.delete(protected_url, expect_errors=True).status_code == 403

    protected_url = '/files/readme?csrf-token={}'.format(admin_csrf_token)
    assert client.delete(protected_url, expect_errors=True).status_code == 403

    protected_url = '/files/readme?csrf-token={}'.format(logged_in_csrf_token)
    assert client.delete(protected_url, expect_errors=True).status_code == 200

    assert client.get('/files/readme', expect_errors=True).status_code == 404
    assert client.delete(
        '/files/readme', expect_errors=True).status_code == 404
