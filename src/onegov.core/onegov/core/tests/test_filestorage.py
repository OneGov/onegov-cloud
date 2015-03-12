import onegov.core
import os.path
import more.webassets

from morepath import setup
from onegov.core import Framework
from webtest import TestApp as Client


def test_independence(tempdir):

    class App(Framework):
        pass

    app = App()
    app.configure_application(
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': tempdir
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

    assert os.path.isdir(os.path.join(tempdir, 'tests-foo'))
    assert os.path.isdir(os.path.join(tempdir, 'tests-bar'))
    assert os.path.isfile(os.path.join(tempdir, 'tests-foo/document.txt'))
    assert os.path.isfile(os.path.join(tempdir, 'tests-bar/document.txt'))


def test_filestorage(tempdir):

    config = setup()

    class App(Framework):
        testing_config = config

    @App.path('/')
    class Model(object):
        pass

    @App.view(model=Model)
    def view_file(self, request):
        return request.filestorage_link(request.params.get('file'))

    config.scan(onegov.core)
    config.scan(more.webassets)
    config.commit()

    app = App()
    app.configure_application(
        filestorage='fs.osfs.OSFS',
        filestorage_options={
            'root_path': tempdir
        }
    )
    app.namespace = 'tests'
    app.set_application_id('tests/foo')
    app.filestorage.setcontents('test.txt', 'asdf')
    app.filestorage.setcontents('readme', 'readme')

    client = Client(app)
    assert client.get('/?file=test.txt').text == '/filestorage/test.txt'
    assert client.get('/?file=asdf.txt').text == ''

    assert client.get('/filestorage/test.txt').text == 'asdf'
    assert client.get('/filestorage/test.txt').content_type == 'text/plain'

    assert client.get('/filestorage/readme').text == 'readme'
    assert client.get('/filestorage/readme').content_type == 'text/plain'

    app.set_application_id('tests/bar')

    client = Client(app)
    assert client.get('/?file=test.txt').text == ''
    assert client.get('/?file=asdf.txt').text == ''
