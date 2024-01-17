from onegov.core.templates import render_macro
from onegov.core.utils import Bunch
from onegov.form import Form
from onegov.org.layout import DefaultLayout
from pyquery import PyQuery as pq
from webob.multidict import MultiDict
from wtforms.fields import StringField


class DummyRequest:

    is_manager = False
    is_admin = False

    def __init__(self, app):
        self.app = app
        self.session = app.session()

    def include(self, value):
        pass

    def translate(self, value, **kwargs):
        return value

    def get_translate(self, for_chameleon=None):
        return self.translate

    def link(self, *args, **kwargs):
        return '#'

    def new_csrf_token(self):
        return ''


def test_form_field_long_description_markdown(org_app):

    model = Bunch()
    request = DummyRequest(org_app)

    layout = DefaultLayout(model, request)

    class LongDescriptionForm(Form):
        text = StringField(
            label='Text',
            description='Short text and md elem is enough [link](#).')

    form = LongDescriptionForm(MultiDict([
        ('text', 'Example')
    ]))
    form.request = DummyRequest(org_app)

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
