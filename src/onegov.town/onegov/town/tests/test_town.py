import onegov.core
import onegov.town
import more.webassets

from morepath import setup
from onegov.town import TownApp
from onegov.town.template import TemplateApi
from webtest import TestApp as Client


def test_template_api():
    # basic tests that can be done by mocking

    class Mock(object):
        pass

    api = TemplateApi(Mock(), Mock())
    api.request.app = 'test'
    assert api.app == 'test'

    api = TemplateApi(Mock(), Mock())
    api.request.path_info = '/'
    assert api.page_id == 'root'

    api = TemplateApi(Mock(), Mock())
    api.request.path_info = '/foo/bar/'
    assert api.page_id == 'foo-bar'


def test_template_layout():
    config = setup()

    class App(TownApp):
        testing_config = config

    @App.path('/model')
    class Model(object):
        pass

    @App.html(model=Model, template='layout.pt')
    def view_model(self, request):
        api = TemplateApi(self, request)
        return {'api': api}

    config.scan(more.webassets)
    config.scan(onegov.core)
    config.scan(onegov.town)
    config.commit()

    app = App()
    app.configure_application(filestorage='fs.memoryfs.MemoryFS')
    app.namespace = 'tests'
    app.set_application_id('tests/foo')

    client = Client(app)
    response = client.get('/model')

    assert '<!DOCTYPE html>' in response.text
    assert '<body id="model"' in response.text
