from __future__ import annotations

from more.webassets import WebassetsApp
from onegov.core.security import Public
from onegov.form import _
from onegov.form.errors import FormError
from onegov.form.parser.core import flatten_fieldsets, parse_formcode
from onegov.form.parser.snippets import Snippets
from onegov.form.utils import disable_required_attribute_in_html_inputs
from yaml.parser import ParserError


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest
    from onegov.core.types import JSON_ro


class FormApp(WebassetsApp):

    def configure_form(self, **cfg: Any) -> None:
        disable_required_attribute_in_html_inputs()


class FormcodeParseFields:
    pass


@FormApp.path(path='formcode-snippets', model=Snippets)
def get_formcode_snippets() -> Snippets:
    return Snippets()


@FormApp.path(path='formcode-fields', model=FormcodeParseFields)
def get_formcode_parse_fields() -> FormcodeParseFields:
    return FormcodeParseFields()


@FormApp.json(model=Snippets, permission=Public)
def view_formcode_snippets(
    self: Snippets,
    request: CoreRequest
) -> JSON_ro:
    return {
        'labels': {
            'required': request.translate(_('Required')),
            'optional': request.translate(_('Optional')),
            'field_comment_example': request.translate(_(
                'Place the field comment beneath the field or choices, '
                'always using the same indentation'))
        },
        'snippets': tuple(self.translated(request))
    }


@FormApp.json(model=FormcodeParseFields, permission=Public,
              request_method='GET')
@FormApp.json(model=FormcodeParseFields, permission=Public,
              request_method='POST')
def view_parse_formcode(
    self: FormcodeParseFields,
    request: CoreRequest
) -> JSON_ro:
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
    except (FormError, AttributeError, TypeError, ParserError):
        return {'error': True}


@FormApp.webasset_path()
def get_js_path() -> str:
    return 'assets/js'


@FormApp.webasset_path()
def get_css_path() -> str:
    return 'assets/css'


@FormApp.webasset('formcode')
def get_formcode_asset() -> Iterator[str]:
    yield 'utils.js'
    yield 'watcher.jsx'
    yield 'togglebutton.jsx'
    yield 'snippets.jsx'
    yield 'format.jsx'
    yield 'select.jsx'


@FormApp.webasset('iconwidget')
def get_iconwidget_asset() -> Iterator[str]:
    yield 'iconwidget.css'
    yield 'iconwidget.js'


@FormApp.webasset('preview-widget-handler')
def get_preview_widget_asset() -> Iterator[str]:
    yield 'preview-widget.css'
    yield 'preview-widget.js'


@FormApp.webasset('text-module-picker')
def get_text_module_picker_asset() -> Iterator[str]:
    yield 'text-module-picker.css'
    yield 'text-module-picker.js'


@FormApp.webasset('lazy-wolves')
def get_honeypot_asset() -> Iterator[str]:
    yield 'honeypot.css'


@FormApp.webasset(
    'chosen',
    filters={'css': ['datauri', 'custom-rcssmin']}
)
def get_chosen_asset() -> Iterator[str]:
    # Make sure your app includes jQuery!
    yield 'chosen.css'
    yield 'chosen.fixes.css'
    yield 'chosen.jquery.js'
    yield 'chosen-init.js'


@FormApp.webasset(
    'treeselect',
    filters={'css': ['datauri', 'custom-rcssmin']}
)
def get_treeselect_asset() -> Iterator[str]:
    yield 'treeselect.css'
    yield 'treeselect.fixes.css'
    yield 'treeselect.js'
    yield 'treeselect-init.js'


@FormApp.webasset('typeahead-standalone')
def get_typeahead_asset() -> Iterator[str]:
    yield 'typeahead-standalone.css'
    yield 'typeahead-standalone.js'
    yield 'typeahead-standalone-init.js'


@FormApp.webasset('multicheckbox')
def get_multicheckbox_asset() -> Iterator[str]:
    yield 'multicheckbox.js'
