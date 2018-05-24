import morepath

from onegov.core import Framework
from onegov.core import filters  # noqa -> registers webasset filters
from onegov.core.utils import scan_morepath_modules
from onegov.quill import QuillApp
from webtest import TestApp as Client


def test_integration(temporary_directory, redis_url):

    class App(Framework, QuillApp):
        pass

    @App.webasset_output()
    def get_output_path():
        return temporary_directory

    @App.path(path='')
    class Root(object):
        pass

    @App.html(model=Root)
    def view_root(self, request):
        request.include('quill')
        return '<body></body>'

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(redis_url=redis_url)
    app.namespace = 'foo'
    app.set_application_id('foo/bar')

    assert 'quill.bundle.js' in Client(app).get('/')
