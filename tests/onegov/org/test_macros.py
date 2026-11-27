from datetime import datetime
from functools import cached_property
from onegov.core.templates import render_macro
from onegov.core.utils import append_query_param, Bunch
from onegov.form import Form
from onegov.org.layout import DefaultLayout
from pyquery import PyQuery as pq  # type: ignore[import-untyped]
from webob.multidict import MultiDict
from wtforms.fields import StringField


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestOrgApp


class DummyRequest:

    is_manager = False
    is_admin = False
    csrf_token = ''
    locale = 'de_CH'

    def __init__(self, app: TestOrgApp) -> None:
        self.app = app
        self.session = app.session()

    def include(self, value: object) -> None:
        pass

    def translate(self, value: str, **kwargs: object) -> str:
        return value

    def get_translate(self, for_chameleon: object = None) -> Any:
        return self.translate

    def link(self, *args: object, **kwargs: object) -> str:
        return '#'

    def new_csrf_token(self) -> str:
        return self.csrf_token

    def csrf_protected_url(self, url: str) -> str:
        return append_query_param(url, 'csrf-token', self.csrf_token)

    @cached_property
    def template_loader(self) -> Any:
        registry = self.app.config.template_engine_registry
        return registry._template_loaders['.pt']


def test_form_field_long_description_markdown(org_app: TestOrgApp) -> None:

    model = Bunch()
    request: Any = DummyRequest(org_app)

    layout = DefaultLayout(model, request)

    class LongDescriptionForm(Form):
        text = StringField(
            label='Text',
            description='Short text and md elem is enough [link](#).')

    form = LongDescriptionForm(MultiDict([
        ('text', 'Example')
    ]))
    form.request = DummyRequest(org_app)  # type: ignore[assignment]

    html = render_macro(
        layout.macros['form'],
        form.request,
        {
            'form': form,
            'layout': layout,
            'year': layout.today().year,
        }
    )
    assert pq(html)('.long-field-help a').attr('href') == '#'
    assert pq(html)('.long-field-help a').text() == 'link'


def test_reservations_resource_title_shown_once(org_app: TestOrgApp) -> None:
    # with multiple reservations the resource title is rendered only once
    request: Any = DummyRequest(org_app)
    layout = DefaultLayout(Bunch(), request)

    def reservation(hour: int) -> Bunch:
        return Bunch(
            display_start=lambda: datetime(2015, 8, 28, hour),
            display_end=lambda: datetime(2015, 8, 28, hour + 1),
            quota=1,
        )

    html = render_macro(layout.macros['reservations'], request, {
        'reservations': [reservation(10), reservation(12), reservation(14)],
        'layout': layout,
        'resource_title': 'Tageskarte',
        'resource_url': 'https://example.org/resource/tageskarte',
    })

    titles = pq(html)('.reservation-resource-title')
    assert len(titles) == 1
    assert titles.text() == 'Tageskarte'
    assert titles('a').attr('href') == 'https://example.org/resource/tageskarte'
    # all three reservations are still rendered
    assert len(pq(html)('.reservations > li')) == 3


def test_reservations_resource_title_without_url(org_app: TestOrgApp) -> None:
    # without a resource url the title renders as plain text, no link
    request: Any = DummyRequest(org_app)
    layout = DefaultLayout(Bunch(), request)
    reservation = Bunch(
        display_start=lambda: datetime(2015, 8, 28, 10),
        display_end=lambda: datetime(2015, 8, 28, 11),
        quota=1,
    )

    html = render_macro(layout.macros['reservations'], request, {
        'reservations': [reservation],
        'layout': layout,
        'resource_title': 'Tageskarte',
    })

    title = pq(html)('.reservation-resource-title')
    assert title.text() == 'Tageskarte'
    assert len(title('a')) == 0


def test_reservations_without_resource_title(org_app: TestOrgApp) -> None:
    # without a resource title no title element is rendered
    request: Any = DummyRequest(org_app)
    layout = DefaultLayout(Bunch(), request)
    reservation = Bunch(
        display_start=lambda: datetime(2015, 8, 28, 10),
        display_end=lambda: datetime(2015, 8, 28, 11),
        quota=1,
    )

    html = render_macro(layout.macros['reservations'], request, {
        'reservations': [reservation],
        'layout': layout,
    })

    assert len(pq(html)('.reservation-resource-title')) == 0
