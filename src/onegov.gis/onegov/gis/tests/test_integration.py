import morepath
import pytest

from onegov.core import Framework
from onegov.core import filters  # noqa -> registers webasset filters
from onegov.core.utils import scan_morepath_modules
from onegov.gis import MapboxApp
from webtest import TestApp as Client


def test_no_secret_keys(temporary_directory):

    class App(Framework, MapboxApp):
        pass

    @App.webasset_output()
    def get_output_path():
        return temporary_directory

    morepath.commit(App)
    app = App()

    with pytest.raises(AssertionError):
        app.configure_application(mapbox_token='sk.asdf')


def test_mapbox_token_tween(temporary_directory, redis_url):

    class App(Framework, MapboxApp):
        pass

    @App.webasset_output()
    def get_output_path():
        return temporary_directory

    @App.path(path='')
    class Root(object):
        pass

    @App.html(model=Root)
    def view_root(self, request):
        return '<body></body>'

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(mapbox_token='pk.asdf', redis_url=redis_url)
    app.namespace = 'foo'
    app.set_application_id('foo/bar')

    assert '<body data-mapbox-token="pk.asdf"></body>' in Client(app).get('/')
