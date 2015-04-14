# -*- coding: utf-8 -*-
from __future__ import print_function

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

        def include(self, *args, **kwargs):
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
        theme_options = {}

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


def test_login(town_app):
    client = Client(town_app)

    links = pq(client.get('/').text).find('.bottom-links a')
    assert links[1].text == 'Login'

    login_page = client.get(links[1].attrib.get('href'))
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = ''
    login_page = login_page.form.submit()

    assert u"Dieses Feld wird benötigt" in login_page.text

    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'wrong'
    login_page = login_page.form.submit()

    assert "Unbekannter Benutzername oder falsches Passwort" in login_page.text

    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'

    index_page = login_page.form.submit().follow()
    assert "Sie wurden eingeloggt" in index_page.text

    links = pq(index_page.text).find('.bottom-links a')
    assert links[1].text == 'Logout'

    index_page = client.get(links[1].attrib.get('href')).follow()
    assert "Sie wurden ausgeloggt" in index_page.text

    links = pq(index_page.text).find('.bottom-links a')
    assert links[1].text == 'Login'


def test_settings(town_app):
    client = Client(town_app)

    assert client.get('/settings', expect_errors=True).status_code == 403

    login_page = client.get('/login')
    login_page.form['email'] = 'admin@example.org'
    login_page.form['password'] = 'hunter2'
    login_page.form.submit()

    settings_page = client.get('/settings')
    document = pq(settings_page.text)
    
    assert document.find('input[name=name]').val() == 'Govikon'
    assert document.find('input[name=primary_color]').val() == '#006fba'

    settings_page.form['primary_color'] = '#xxx'
    settings_page = settings_page.form.submit()

    assert "Ungültige Farbe." in settings_page.text

    settings_page.form['primary_color'] = '#ccddee'
    settings_page = settings_page.form.submit()

    assert not "Ungültige Farbe." in settings_page.text
