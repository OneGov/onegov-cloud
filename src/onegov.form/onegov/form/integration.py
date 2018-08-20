from more.webassets import WebassetsApp
from onegov.core.security import Public
from onegov.form import _
from onegov.form.parser.core import flatten_fieldsets, parse_formcode
from onegov.form.parser.snippets import Snippets
from onegov.form.errors import FormError
from onegov.form.utils import use_required_attribute_in_html_inputs


class FormApp(WebassetsApp):

    def configure_form(self, **cfg):
        # disable the required attribute in html forms as introduced by
        # wtforms 2.2 - we do our own thing here
        use_required_attribute_in_html_inputs(False)


class FormcodeParseFields(object):
    pass


@FormApp.path(path='formcode-snippets', model=Snippets)
def get_formcode_snippets():
    return Snippets()


@FormApp.path(path='formcode-fields', model=FormcodeParseFields)
def get_formcode_parse_fields():
    return FormcodeParseFields()


@FormApp.json(model=Snippets, permission=Public)
def view_formcode_snippets(self, request):
    return {
        'labels': {
            'required': request.translate(_("Required")),
            'optional': request.translate(_("Optional")),
        },
        'snippets': tuple(self.translated(request))
    }


@FormApp.json(model=FormcodeParseFields, permission=Public,
              request_method='GET')
@FormApp.json(model=FormcodeParseFields, permission=Public,
              request_method='POST')
def view_parse_formcode(self, request):
    formcode = request.params.get('formcode') or request.text

    if not formcode:
        return {}

    try:
        return [
            {
                'id': field.id,
                'human_id': field.human_id,
                'type': field.type,
            }
            for field in flatten_fieldsets(parse_formcode(formcode))
        ]
    except (FormError, AttributeError, TypeError):
        return {'error': True}

    return []


@FormApp.webasset_path()
def get_js_path():
    return 'assets/js'


@FormApp.webasset_path()
def get_css_path():
    return 'assets/css'


@FormApp.webasset('formcode')
def get_formcode_asset():
    yield 'utils.js'
    yield 'watcher.jsx'
    yield 'togglebutton.jsx'
    yield 'snippets.jsx'
    yield 'format.jsx'
    yield 'select.jsx'


@FormApp.webasset('iconwidget')
def get_iconwidget_asset():
    yield 'iconwidget.css'
    yield 'iconwidget.js'
