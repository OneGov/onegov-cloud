from __future__ import annotations

import morepath
import requests

from babel import Locale
from onegov.core.custom import json
from onegov.core.elements import Intercooler, Link
from onegov.core.security import Private, Public
from onegov.core.utils import normalize_for_url
from onegov.fedpol import _, FedpolApp
from onegov.fedpol.models import FormSubmissionStep
from onegov.fedpol.layout import FormSubmissionLayout, FormSubmissionStepLayout
from onegov.fedpol.utils import get_step_form
from onegov.form import FormCollection, FormDefinition
from onegov.gis import Coordinates
from onegov.org.models import CustomFormDefinition
from onegov.org.views.form_definition import get_hints, get_form_class
from onegov.town6.layout import FormEditorLayout
from webob.exc import HTTPNotFound


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fedpol.request import FedpolRequest
    from onegov.form import Form
    from onegov.org.forms import FormDefinitionForm
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


TRANSLATE_SYSTEM_PROMPT = """\
You are an expert translator working for the Swiss government and are tasked
with translating forms from {from_locale} to {to_locale}.

You are also very familiar with formcode, the specialized Markdown inspired
syntax for defining forms. When translating forms you need to take special
care to preserve the semantic structure of formcode.

The user prompt will give you a JSON object with all of the strings that need
to be translated. Pay special attention to the "definition" key which contains
formcode, when translating this field keep the structure exactly the same,
ensure the translated formcode is still valid syntax, pay close attention to
date and time fields, which will always have the same format string, regardless
of the target language. Furthermore the "text" key will contain HTML, here once
again make sure to generate valid HTML, with the same semantic structure.

Respond with a JSON object that contains all of the translated strings.

When translating strings be honest and reproduce the original intent, do not
invent new text or alter the meaning of existing text in any way.

Here is the complete specification of the aforementioned formcode:

{specification}
"""


def get_defined_form_class(
    self: FormDefinition,
    request: FedpolRequest
) -> type[Form]:

    if request.is_manager:
        return self.form_class
    step_form_class = get_step_form(self, 1)
    if step_form_class is None:
        # NOTE: This shouldn't happen, but just in case we handle it
        return self.form_class
    return step_form_class


@FedpolApp.form(
    model=FormDefinition,
    template='form.pt',
    permission=Public,
    form=get_defined_form_class
)
def handle_defined_form(
    self: FormDefinition,
    request: FedpolRequest,
    form: Form,
) -> RenderData | Response:
    """ Renders the empty form and takes input, even if it's not valid, stores
    it as a pending submission and redirects the user to the view that handles
    pending submissions.

    """

    if not request.is_manager and hasattr(self, 'localized_url'):
        localized_url = self.localized_url(request)
        if localized_url:
            return morepath.redirect(localized_url)

    has_steps = getattr(form, 'is_step', False)
    collection = FormCollection(request.session)

    if not self.current_registration_window:
        spots = 0
        enabled = True
    else:
        spots = 1
        enabled = self.current_registration_window.accepts_submissions(spots)

    if enabled and request.POST:
        submission = collection.submissions.add(
            self.name, form, state='pending', spots=spots)

        if has_steps:
            step = FormSubmissionStep(submission, step=1)
            if form.validate():
                next_step = step.next_step
                if next_step is None:
                    next_url = request.link(submission)
                else:
                    next_url = request.link(next_step)
            else:
                next_url = request.link(
                    step,
                    # NOTE: Forces display of validation errors
                    query_params={'submitted': '1'}
                )
        else:
            next_url = request.link(submission)

        return morepath.redirect(next_url)

    layout = FormSubmissionStepLayout(
        self,
        request,
        title=self.title,
        step_title=getattr(form, 'step_name', None)
    ) if has_steps else FormSubmissionLayout(self, request, title=self.title)

    return {
        'layout': layout,
        'title': self.title,
        'form': enabled and form,
        'definition': self,
        'form_width': 'small',
        'lead': layout.linkify(self.meta.get('lead')),
        'text': self.text,
        'people': getattr(self, 'people', None),
        'files': getattr(self, 'files', None),
        'contact': getattr(self, 'contact_html', None),
        'coordinates': getattr(self, 'coordinates', Coordinates()),
        'hints': tuple(get_hints(layout, self.current_registration_window)),
        'hints_callout': not enabled,
        'button_text': _('Continue')
    }


@FedpolApp.form(
    model=CustomFormDefinition,
    template='form.pt',
    permission=Private,
    form=get_form_class,
    pass_model=True,
    name='translate'
)
def handle_translate_definition(
    self: CustomFormDefinition,
    request: FedpolRequest,
    form: FormDefinitionForm
) -> RenderData | Response:

    locale = request.GET.get('locale')
    if locale not in request.app.locales or self.locale is None:
        raise HTTPNotFound()

    # NOTE: If a translation already exists, redirect to it
    if locale in self.alt_locale_ids:
        return morepath.redirect(request.class_link(
            FormDefinition,
            {'name': self.meta['alt_locale_ids'][locale]},
            name='edit'
        ))

    api_key = request.app.infomaniak_api_token
    product_id = request.app.infomaniak_product_id
    can_translate = api_key is not None and product_id is not None
    collection = FormCollection(request.session)
    if form.submitted(request):
        assert form.title.data is not None
        assert form.definition.data is not None

        if collection.definitions.by_name(normalize_for_url(form.title.data)):
            request.alert(_('A form with this name already exists'))
        else:
            definition = collection.definitions.add(
                title=form.title.data,
                definition=form.definition.data,
                type='custom'
            )
            assert isinstance(definition, CustomFormDefinition)
            with request.session.no_autoflush:
                form.populate_obj(definition)
                definition.locale = locale
                # link existing translations to new translation
                definition.alt_locale_ids = self.alt_locale_ids.copy()
                definition.alt_locale_ids[self.locale] = self.name

                # link new translation to other linked translations
                for form_name in self.alt_locale_ids.values():
                    existing = request.session.get(
                        CustomFormDefinition,
                        form_name
                    )
                    if existing is None:
                        continue

                    alt_locale_ids = existing.alt_locale_ids
                    alt_locale_ids[locale] = definition.name
                    existing.alt_locale_ids = alt_locale_ids

                # link new translation to source translation
                alt_locale_ids = self.alt_locale_ids
                alt_locale_ids[locale] = definition.name
                self.alt_locale_ids = alt_locale_ids

            request.success(_('Added a new form'))
            return morepath.redirect(request.link(definition))
    elif (
        can_translate
        and not request.POST
        and request.GET.get('translate') == '1'
    ):
        # NOTE: Hide the AI translate button after translation
        can_translate = False
        url = (
            f'https://api.infomaniak.com/1/ai/{product_id}'
            f'/openai/chat/completions'
        )
        system_prompt = TRANSLATE_SYSTEM_PROMPT.format(
            from_locale=self.locale,
            to_locale=locale,
            specification=request.app.formcode_specification,
        )
        payload = {
            key: value
            for key in (
                'title',
                'lead',
                'text',
                'group',
                'definition',
                'pick_up',
                'custom_above_footer'
            )
            if isinstance((value := form[key].data), str)
        }
        result = requests.post(
            url,
            headers={
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json',
            },
            json={
                'model': 'qwen3',
                'messages': [
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': json.dumps(payload)}
                ],
                'temperature': 0,
                'response_format': {
                    'type': 'json_schema',
                    'json_schema': {
                        'name': 'translation_output',
                        'schema': {
                            'type': 'object',
                            'properties': {
                                key: {'type': 'string'}
                                for key in payload
                            }
                        }
                    }
                }
            },
            timeout=30,
        ).json()
        translated = json.loads(result['choices'][0]['message']['content'])
        for key, value in translated.items():
            form[key].data = value

    language = Locale.parse(locale).get_language_name(request.locale)
    if language is None:
        language = locale
    title = _('Translate to ${language}', mapping={'language': language})
    layout = FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.link(collection)),
        Link(self.title, request.link(self)),
        Link(title, '#')
    ]
    layout.edit_mode = True
    if can_translate:
        layout.editmode_links.insert(1, Link(
            text=_('AI Translate'),
            url=request.link(self, 'translate', query_params={
                'locale': locale,
                'translate': '1'
            }),
            traits=(
                Intercooler('GET', 'main'),
            ),
            attrs={
                'class': 'translate-link',
                'ic-action-target': 'this',
                'ic-beforeSend-action': 'addClass:in-progress',
                'ic-select-from-response': 'main',
            }
        ))

    return {
        'layout': layout,
        'title': title,
        'form': form,
        'form_width': 'large',
    }


@FedpolApp.form(
    model=CustomFormDefinition,
    template='form.pt',
    permission=Private,
    form=get_form_class,
    pass_model=True,
    name='duplicate'
)
def handle_duplicate_definition(
    self: CustomFormDefinition,
    request: FedpolRequest,
    form: FormDefinitionForm
) -> RenderData | Response:

    collection = FormCollection(request.session)
    if form.submitted(request):
        assert form.title.data is not None
        assert form.definition.data is not None

        if collection.definitions.by_name(normalize_for_url(form.title.data)):
            request.alert(_('A form with this name already exists'))
        else:
            definition = collection.definitions.add(
                title=form.title.data,
                definition=form.definition.data,
                type='custom'
            )
            assert isinstance(definition, CustomFormDefinition)
            with request.session.no_autoflush:
                form.populate_obj(definition)
                definition.locale = self.locale

            request.success(_('Added a new form'))
            return morepath.redirect(request.link(definition))
    elif not request.POST:
        if form.title.data:
            # FIXME: i18n
            form.title.data += ' Kopie'

    layout = FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.link(collection)),
        Link(self.title, request.link(self)),
        Link(_('Duplicate'), '#')
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('Duplicate'),
        'form': form,
        'form_width': 'large',
    }
