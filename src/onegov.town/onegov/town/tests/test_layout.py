# -*- coding: utf-8 -*-
import onegov.core
import onegov.town
import more.transaction
import more.webassets

from datetime import datetime
from morepath import setup
from onegov.page import Page
from onegov.town import TownApp
from onegov.town.layout import (
    EventBaseLayout,
    Layout,
    PageLayout
)
from webtest import TestApp as Client


class MockModel(object):
    pass


class MockRequest(object):
    locale = 'en'

    def include(self, *args, **kwargs):
        pass

    def link(self, model):
        if isinstance(model, Page):
            return model.path

    def exclude_invisible(self, objects):
        return objects


def test_layout():
    # basic tests that can be done by mocking

    layout = Layout(MockModel(), MockRequest())
    layout.request.app = 'test'
    assert layout.app == 'test'

    layout = Layout(MockModel(), MockRequest())
    layout.request.path_info = '/'
    assert layout.page_id == 'root'

    layout = Layout(MockModel(), MockRequest())
    layout.request.path_info = '/foo/bar/'
    assert layout.page_id == 'foo-bar'


def test_page_layout_sidebar(session):
    page = Page(
        name='grandma',
        title='Grandma',
        type='topic',
        children=[
            Page(
                name='ma',
                title='Ma',
                type='topic',
                children=[
                    Page(
                        name='ada',
                        title='Ada',
                        type='topic'
                    )
                ]
            )
        ]
    )
    session.add(page)

    layout = PageLayout(page, MockRequest())
    layout.homepage_url = 'http://nohost'

    assert len(layout.sidebar_links) == 3

    assert layout.sidebar_links[0].url == 'grandma'
    assert layout.sidebar_links[0].text == 'Grandma'
    assert layout.sidebar_links[0].active

    assert layout.sidebar_links[1].url == 'grandma/ma'
    assert layout.sidebar_links[1].text == 'Ma'
    assert layout.sidebar_links[1].classes == ('childpage', )

    assert layout.sidebar_links[2].url == '#'
    assert layout.sidebar_links[2].text == '...'
    assert layout.sidebar_links[2].classes == ('new-content-placeholder', )

    layout = PageLayout(page.children[0], MockRequest())

    assert len(layout.sidebar_links) == 3

    assert layout.sidebar_links[0].url == 'grandma/ma'
    assert layout.sidebar_links[0].text == 'Ma'
    assert layout.sidebar_links[0].active

    assert layout.sidebar_links[1].url == 'grandma/ma/ada'
    assert layout.sidebar_links[1].text == 'Ada'
    assert layout.sidebar_links[1].classes == ('childpage', )

    assert layout.sidebar_links[2].url == '#'
    assert layout.sidebar_links[2].text == '...'
    assert layout.sidebar_links[2].classes == ('new-content-placeholder', )

    layout = PageLayout(page.children[0].children[0], MockRequest())

    assert len(layout.sidebar_links) == 2

    assert layout.sidebar_links[0].url == 'grandma/ma/ada'
    assert layout.sidebar_links[0].text == 'Ada'
    assert layout.sidebar_links[0].active

    assert layout.sidebar_links[1].url == '#'
    assert layout.sidebar_links[1].text == '...'
    assert layout.sidebar_links[1].classes == ('new-content-placeholder', )


def test_page_layout_breadcrumbs(session):
    page = Page(
        name='grandma',
        title='Grandma',
        children=[
            Page(
                name='ma',
                title='Ma',
                children=[
                    Page(
                        name='ada',
                        title='Ada'
                    )
                ]
            )
        ]
    )
    session.add(page)

    layout = PageLayout(page, MockRequest())
    layout.homepage_url = 'http://nohost'

    links = layout.breadcrumbs
    assert len(links) == 2
    assert links[0].text == 'Homepage'
    assert links[0].url == 'http://nohost'
    assert links[1].text == 'Grandma'
    assert links[1].url == 'grandma'

    layout = PageLayout(page.children[0], MockRequest())
    layout.homepage_url = 'http://nohost'

    links = layout.breadcrumbs
    assert len(links) == 3
    assert links[0].text == 'Homepage'
    assert links[0].url == 'http://nohost'
    assert links[1].text == 'Grandma'
    assert links[1].url == 'grandma'
    assert links[2].text == 'Ma'
    assert links[2].url == 'grandma/ma'


def test_template_layout():
    config = setup()

    class Mock(object):
        pass

    class App(TownApp):
        testing_config = config
        theme_options = {}

        town = Mock()
        town.name = 'Govikon'

        # disable LibresIntegration for this test
        def configure_libres(self, **cfg):
            pass

    @App.path('/model')
    class Model(object):
        pass

    @App.html(model=Model, template='layout.pt')
    def view_model(self, request):
        layout = Layout(self, request)
        layout.homepage_url = None
        layout.font_awesome_path = ''
        return {'layout': layout}

    config.scan(more.transaction)
    config.scan(more.webassets)
    config.scan(onegov.core)
    config.scan(onegov.town)
    config.commit()

    app = App()
    app.namespace = 'tests'
    app.configure_application(dsn=None, filestorage='fs.memoryfs.MemoryFS')
    app.set_application_id('tests/foo')

    client = Client(app)
    response = client.get('/model')

    assert '<!DOCTYPE html>' in response.text
    assert '<body id="model"' in response.text


def test_events_layout_format_date():
    then = datetime(2015, 7, 5, 10, 15)
    request = MockRequest()

    layout = EventBaseLayout(MockModel(), request)
    assert layout.format_date(then, 'weekday') == 'Sunday'
    assert layout.format_date(then, 'month') == 'July'
    assert layout.format_date(then, 'event') == 'Sunday, 5. July 2015, 10:15'

    request.locale = 'de'
    layout = EventBaseLayout(MockModel(), request)
    assert layout.format_date(then, 'date') == '05.07.2015'
    assert layout.format_date(then, 'datetime') == '05.07.2015 10:15'
    assert layout.format_date(then, 'time') == '10:15'
    assert layout.format_date(then, 'weekday') == 'Sonntag'
    assert layout.format_date(then, 'month') == 'Juli'
    assert layout.format_date(then, 'event') == 'Sonntag, 5. Juli 2015, 10:15'
