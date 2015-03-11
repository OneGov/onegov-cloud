import os.path

from onegov.core import Framework


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
