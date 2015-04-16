# -*- coding: utf-8 -*-
from __future__ import print_function

import onegov.core
import onegov.town
import more.webassets

from morepath import setup
from onegov.town import TownApp
from onegov.town.layout import Layout
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
        layout.homepage_url = None
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
