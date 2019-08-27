import morepath
import os.path
import time

from onegov.core.framework import Framework
from onegov.core import utils
from onegov.core.static import StaticFile
from webtest import TestApp as Client


def test_static_file(temporary_directory):

    class App(Framework):
        serve_static_files = True

    @App.static_directory()
    def get_static_files():
        return temporary_directory

    morepath.commit(App)

    app = App()
    app.configure_application()
    app.namespace = 'test'
    app.set_application_id('test/test')

    with open(os.path.join(temporary_directory, 'robots.txt'), 'w') as f:
        f.write('foobar')

    app.serve_static_files = False
    assert StaticFile.from_application(app, 'robots.txt') is None

    app.serve_static_files = True
    assert StaticFile.from_application(app, 'robots.txt').path == 'robots.txt'
    assert StaticFile.from_application(app, '../robots.txt') is None


def test_static_file_app(temporary_directory, redis_url):

    class App(Framework):
        serve_static_files = True

    @App.static_directory()
    def get_static_files():
        return temporary_directory

    utils.scan_morepath_modules(App)
    morepath.commit(App)

    with open(os.path.join(temporary_directory, 'robots.txt'), 'w') as f:
        f.write('foobar')

    app = App()
    app.configure_application(redis_url=redis_url)
    app.namespace = 'test'
    app.set_application_id('test/test')

    c = Client(app)
    assert c.get('/static/robots.txt').text == 'foobar'

    # make sure the if-modified-since header is honored
    timestamp = time.gmtime(time.time() + 1)
    modified = time.strftime('%a, %d %b %Y %H:%M:%S GMT', timestamp)
    headers = {'If-Modified-Since': modified}

    response = c.get('/static/robots.txt', headers=headers, expect_errors=True)
    assert response.status_code == 304

    # make sure inexistant files return a 404
    assert c.get('/static/humans.txt', expect_errors=True).status_code == 404

    # makre sure versioned files are cached forever
    response = c.get('/static/robots.txt')
    assert 'Cache-Control' not in response.headers

    response = c.get('/static/robots.txt___v1.0')
    assert response.headers['Cache-Control'] == 'max-age=31536000'


def test_root_file_app(temporary_directory, redis_url):
    class App(Framework):
        serve_static_files = True

    @App.static_directory()
    def get_static_files():
        return temporary_directory

    class RobotsTxt(StaticFile):
        pass

    @App.path(model=RobotsTxt, path='robots.txt')
    def get_favicon(app, absorb):
        return StaticFile.from_application(app, 'robots.txt')

    utils.scan_morepath_modules(App)
    morepath.commit(App)

    with open(os.path.join(temporary_directory, 'robots.txt'), 'w') as f:
        f.write('foobar')

    app = App()
    app.configure_application(redis_url=redis_url)
    app.namespace = 'test'
    app.set_application_id('test/test')

    c = Client(app)
    assert c.get('/robots.txt').text == 'foobar'


def test_static_files_directive(temporary_directory, redis_url):

    a = os.path.join(temporary_directory, 'a')
    b = os.path.join(temporary_directory, 'b')

    for path in (a, b):
        os.mkdir(path)

        with open(os.path.join(path, 'foobar.txt'), 'w') as f:
            f.write(path)

    class A(Framework):
        serve_static_files = True

    class B(A):
        serve_static_files = True

    @A.static_directory()
    def get_static_files_a():
        return a

    @B.static_directory()
    def get_static_files_b():
        return b

    utils.scan_morepath_modules(A)
    utils.scan_morepath_modules(B)

    morepath.commit(A)
    morepath.commit(B)

    app_a = A()
    app_b = B()

    for app in (app_a, app_b):
        app.configure_application(redis_url=redis_url)
        app.namespace = 'test'
        app.set_application_id('test/test')

    assert app_a.static_files == [a]
    assert app_b.static_files == [b, a]

    assert Client(app_a).get('/static/foobar.txt').text == a
    assert Client(app_b).get('/static/foobar.txt').text == b
