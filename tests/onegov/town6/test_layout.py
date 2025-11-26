from __future__ import annotations

import onegov.core
import onegov.org
import more.transaction
import more.webassets
import morepath

from datetime import datetime
from onegov.core.elements import Link
from onegov.core.utils import Bunch
from onegov.page import Page
from onegov.town6 import TownApp
from onegov.town6.layout import DefaultLayout, PageLayout
from webtest import TestApp as Client


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from sqlalchemy.orm import Session


class MockModel:
    pass


class MockRequest:
    locale = 'en'
    is_logged_in = False
    is_manager = False
    app: Any = Bunch(
        org=Bunch(
            geo_provider='geo-mapbox',
            open_files_target_blank=True,
            disable_chat=None,
            chat_customer_id=None
        ),
        version='1.0',
        sentry_dsn=None
    )

    def include(self, *args: object, **kwargs: object) -> None:
        pass

    def link(self, model: object) -> str | None:
        if isinstance(model, Page):
            return model.path
        return None

    def exclude_invisible(self, objects: Any) -> Any:
        return objects


def test_layout() -> None:
    # basic tests that can be done by mocking

    layout = DefaultLayout(MockModel(), MockRequest())  # type: ignore[arg-type]
    layout.request.app = 'test'  # type: ignore[assignment]
    assert layout.app == 'test'  # type: ignore[comparison-overlap]

    layout = DefaultLayout(MockModel(), MockRequest())  # type: ignore[arg-type]
    layout.request.path_info = '/'
    assert layout.page_id == 'page-root'

    layout = DefaultLayout(MockModel(), MockRequest())  # type: ignore[arg-type]
    layout.request.path_info = '/foo/bar/'
    assert layout.page_id == 'page-foo-bar'


def test_page_layout_sidebar(session: Session) -> None:
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

    layout = PageLayout(page, MockRequest())  # type: ignore[arg-type]
    layout.homepage_url = 'http://nohost'

    assert len(layout.sidebar_links) == 1
    assert layout.sidebar_links[0].title == 'Grandma'
    assert layout.sidebar_links[0].model == page
    assert layout.sidebar_links[0].links == (
        Link(
            text='Ma', url='grandma/ma', model=page.children[0]
        ),
    )

    layout = PageLayout(page.children[0], MockRequest())  # type: ignore[arg-type]

    assert len(layout.sidebar_links) == 1
    assert layout.sidebar_links[0].title == 'Ma'
    assert layout.sidebar_links[0].model == page.children[0]
    assert layout.sidebar_links[0].links == (
        Link(
            text='Ada', url='grandma/ma/ada',
            model=page.children[0].children[0]
        ),
    )

    layout = PageLayout(page.children[0].children[0], MockRequest())  # type: ignore[arg-type]

    assert len(layout.sidebar_links) == 1
    assert layout.sidebar_links[0].title == 'Ada'
    assert layout.sidebar_links[0].model == page.children[0].children[0]
    assert not layout.sidebar_links[0].links


def test_page_layout_breadcrumbs(session: Session) -> None:
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

    layout = PageLayout(page, MockRequest())  # type: ignore[arg-type]
    layout.homepage_url = 'http://nohost'

    links = layout.breadcrumbs
    assert len(links) == 2
    assert links[0].text == 'Homepage'
    assert links[0].attrs['href'] == 'http://nohost'
    assert links[1].text == 'Grandma'
    assert links[1].attrs['href'] == 'grandma'

    layout = PageLayout(page.children[0], MockRequest())  # type: ignore[arg-type]
    layout.homepage_url = 'http://nohost'

    links = layout.breadcrumbs
    assert len(links) == 3
    assert links[0].text == 'Homepage'
    assert links[0].attrs['href'] == 'http://nohost'
    assert links[1].text == 'Grandma'
    assert links[1].attrs['href'] == 'grandma'
    assert links[2].text == 'Ma'
    assert links[2].attrs['href'] == 'grandma/ma'


def test_template_layout(postgres_dsn: str, redis_url: str) -> None:

    class Mock:
        homepage_structure = ''
        chat_type = None
        chat_customer_id = None
        disable_chat = False

    class App(TownApp):
        theme_options = {}
        header_options: Any = {}

        org: Any = Mock()
        org.name = 'Govikon'
        org.theme_options = theme_options
        org.locales = ['de_CH']
        org.geo_provider = 'geo-mapbox'
        org.open_files_target_blank = True
        org.header_options = header_options
        org.always_show_partners = False
        org.citizen_login_enabled = False

        # disable LibresIntegration for this test
        def configure_libres(self, **cfg: Any) -> None:
            pass

    @App.setting(section='cronjobs', name='enabled')
    def get_cronjobs_enabled() -> bool:
        return False

    @App.path('/model')
    class Model:
        pass

    @App.html(model=Model, template='layout.pt')
    def view_model(self: Model, request: TownRequest) -> RenderData:
        layout = DefaultLayout(self, request)
        layout.homepage_url = None  # type: ignore[assignment]
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


def test_default_layout_format_date() -> None:
    then = datetime(2015, 7, 5, 10, 15)
    request: Any = MockRequest()

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


def test_layout_get_filename_without_extension() -> None:
    layout = DefaultLayout(MockModel(), MockRequest())  # type: ignore[arg-type]
    assert layout.get_filename_without_extension(
        'document.pdf') == 'document'
    assert layout.get_filename_without_extension(
        'no_extension') == 'no_extension'
    assert layout.get_filename_without_extension(
        '.hiddenfile') == '.hiddenfile'
    assert layout.get_filename_without_extension(
        'archive.tar.gz') == 'archive'
    assert layout.get_filename_without_extension(
        'WORD.DOCX') == 'WORD'

    for ext in layout.file_extension_fa_icon_mapping.keys():
        filename = f'file.{ext}'
        name_without_ext = layout.get_filename_without_extension(filename)
        assert name_without_ext == 'file', f'Failed for extension: {ext}'


def test_layout_get_file_extension() -> None:
    layout = DefaultLayout(MockModel(), MockRequest())  # type: ignore[arg-type]
    assert layout.get_filename_extension('document.pdf') == 'pdf'
    assert layout.get_filename_extension('no_extension') == ''
    assert layout.get_filename_extension('.hiddenfile') == ''
    assert layout.get_filename_extension('archive.tar.gz') == 'tar.gz'
    assert layout.get_filename_extension('WORD.DOCX') == 'docx'

    for ext in layout.file_extension_fa_icon_mapping.keys():
        filename = f'file.{ext}'
        extracted_ext = layout.get_filename_extension(filename)
        assert extracted_ext == ext, f'Failed for extension: {ext}'


def test_layout_get_fa_file_icon() -> None:
    layout = DefaultLayout(MockModel(), MockRequest())  # type: ignore[arg-type]
    assert layout.get_fa_file_icon('document.pdf') == 'fa-file-pdf'
    assert layout.get_fa_file_icon('no_extension') == 'fa-file'
    assert layout.get_fa_file_icon('.hiddenfile') == 'fa-file'
    assert layout.get_fa_file_icon('archive.tar.gz') == 'fa-file-zip'

    for ext, icon in layout.file_extension_fa_icon_mapping.items():
        filename = f'file.{ext}'
        fa_icon = layout.get_fa_file_icon(filename)
        assert fa_icon == icon, f'Failed for extension: {ext}'
