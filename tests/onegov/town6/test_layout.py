from datetime import datetime

import morepath

from onegov.core.elements import Link
from onegov.core.utils import Bunch
from onegov.page import Page
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout, PageLayout
import onegov.core
import onegov.org
import more.transaction
import more.webassets
from webtest import TestApp as Client


class MockModel:
    pass


class MockRequest:
    locale = 'en'
    is_logged_in = False
    is_manager = False
    app = Bunch(
        org=Bunch(
            geo_provider='geo-mapbox',
            open_files_target_blank=True,
            disable_chat=None,
            chat_customer_id=None
        ),
        version='1.0',
        sentry_dsn=None
    )

    def include(self, *args, **kwargs):
        pass

    def link(self, model):
        if isinstance(model, Page):
            return model.path

    def exclude_invisible(self, objects):
        return objects


def test_layout():
    # basic tests that can be done by mocking

    layout = DefaultLayout(MockModel(), MockRequest())
    layout.request.app = 'test'
    assert layout.app == 'test'

    layout = DefaultLayout(MockModel(), MockRequest())
    layout.request.path_info = '/'
    assert layout.page_id == 'page-root'

    layout = DefaultLayout(MockModel(), MockRequest())
    layout.request.path_info = '/foo/bar/'
    assert layout.page_id == 'page-foo-bar'


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

    assert len(layout.sidebar_links) == 1
    assert layout.sidebar_links[0].title == 'Grandma'
    assert layout.sidebar_links[0].model == page
    assert layout.sidebar_links[0].links == (
        Link(
            text='Ma', url='grandma/ma', model=page.children[0]
        ),
    )

    layout = PageLayout(page.children[0], MockRequest())

    assert len(layout.sidebar_links) == 1
    assert layout.sidebar_links[0].title == 'Ma'
    assert layout.sidebar_links[0].model == page.children[0]
    assert layout.sidebar_links[0].links == (
        Link(
            text='Ada', url='grandma/ma/ada',
            model=page.children[0].children[0]
        ),
    )

    layout = PageLayout(page.children[0].children[0], MockRequest())

    assert len(layout.sidebar_links) == 1
    assert layout.sidebar_links[0].title == 'Ada'
    assert layout.sidebar_links[0].model == page.children[0].children[0]
    assert not layout.sidebar_links[0].links


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
    assert links[0].attrs['href'] == 'http://nohost'
    assert links[1].text == 'Grandma'
    assert links[1].attrs['href'] == 'grandma'

    layout = PageLayout(page.children[0], MockRequest())
    layout.homepage_url = 'http://nohost'

    links = layout.breadcrumbs
    assert len(links) == 3
    assert links[0].text == 'Homepage'
    assert links[0].attrs['href'] == 'http://nohost'
    assert links[1].text == 'Grandma'
    assert links[1].attrs['href'] == 'grandma'
    assert links[2].text == 'Ma'
    assert links[2].attrs['href'] == 'grandma/ma'


def test_template_layout(postgres_dsn, redis_url):

    class Mock:
        homepage_structure = ''
        chat_type = None
        chat_customer_id = None
        disable_chat = False

    class App(TownApp):
        theme_options = {}
        header_options = {}

        org = Mock()
        org.name = 'Govikon'
        org.theme_options = theme_options
        org.locales = ['de_CH']
        org.geo_provider = 'geo-mapbox'
        org.open_files_target_blank = True
        org.header_options = header_options
        org.always_show_partners = False
        org.citizen_login_enabled = False

        # disable LibresIntegration for this test
        def configure_libres(self, **cfg):
            pass

    @App.setting(section='cronjobs', name='enabled')
    def get_cronjobs_enabled():
        return False

    @App.path('/model')
    class Model:
        pass

    @App.html(model=Model, template='layout.pt')
    def view_model(self, request):
        layout = DefaultLayout(self, request)
        layout.homepage_url = None
        layout.font_awesome_path = ''
        layout.og_image_source = None
        return {'layout': layout}

    morepath.scan(more.transaction)
    morepath.scan(more.webassets)
    morepath.scan(onegov.core)
    morepath.scan(onegov.org)
    morepath.commit(App)

    app = App()
    app.namespace = 'tests'
    app.configure_application(
        dsn=postgres_dsn,
        filestorage='fs.memoryfs.MemoryFS',
        enable_elasticsearch=False,
        depot_backend='depot.io.memory.MemoryFileStorage',
        redis_url=redis_url,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    app.set_application_id('tests/foo')

    client = Client(app)
    response = client.get('/model')

    assert '<!DOCTYPE html>' in response.text
    assert '<body id="page-model"' in response.text


def test_default_layout_format_date():
    then = datetime(2015, 7, 5, 10, 15)
    request = MockRequest()

    layout = DefaultLayout(MockModel(), request)
    assert layout.format_date(then, 'weekday_long') == 'Sunday'
    assert layout.format_date(then, 'month_long') == 'July'
    assert layout.format_date(then, 'event') == 'Sunday, 5. July 2015'

    request.locale = 'de'
    layout = DefaultLayout(MockModel(), request)
    assert layout.format_date(then, 'date') == '05.07.2015'
    assert layout.format_date(then, 'datetime') == '05.07.2015 10:15'
    assert layout.format_date(then, 'time') == '10:15'
    assert layout.format_date(then, 'weekday_long') == 'Sonntag'
    assert layout.format_date(then, 'month_long') == 'Juli'
    assert layout.format_date(then, 'event') == 'Sonntag, 5. Juli 2015'
