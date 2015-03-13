import onegov.core
import onegov.town
import more.webassets

from morepath import setup
from onegov.town import TownApp
from onegov.town.layout import Layout
from pyquery import PyQuery as pq
from webtest import TestApp as Client


def test_layout():
    # basic tests that can be done by mocking

    class Mock(object):
        pass

    layout = Layout(Mock(), Mock())
    layout.request.app = 'test'
    assert layout.app == 'test'

    layout = Layout(Mock(), Mock())
    layout.request.path_info = '/'
    assert layout.page_id == 'root'

    layout = Layout(Mock(), Mock())
    layout.request.path_info = '/foo/bar/'
    assert layout.page_id == 'foo-bar'


def test_template_layout():
    config = setup()

    class App(TownApp):
        testing_config = config

    @App.path('/model')
    class Model(object):
        pass

    @App.html(model=Model, template='layout.pt')
    def view_model(self, request):
        layout = Layout(self, request)
        return {'layout': layout}

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


def test_startpage(town_app):
    client = Client(town_app)

    links = pq(client.get('/').text).find('.top-bar-section a')

    links[0].text == 'Leben & Wohnen'
    links[0].attrib.get('href') == '/gemeinde/leben-wohnen'

    links[1].text == 'Kultur & Freizeit'
    links[1].attrib.get('href') == '/gemeinde/kultur-freizeit'

    links[2].text == 'Bildung & Gesellschaft'
    links[2].attrib.get('href') == '/gemeinde/bildung-gesellschaft'

    links[3].text == 'Gewerbe & Tourismus'
    links[3].attrib.get('href') == '/gemeinde/gewerbe-tourismus'

    links[4].text == 'Politik & Verwaltung'
    links[4].attrib.get('href') == '/gemeinde/politik-verwaltung'
