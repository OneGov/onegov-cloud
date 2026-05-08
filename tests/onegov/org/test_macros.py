from __future__ import annotations

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
