from __future__ import annotations

import morepath

from babel import Locale
from onegov.core.security import Private, Public
from onegov.core.utils import normalize_for_url
from onegov.fedpol import _, FedpolApp
from onegov.fedpol.models import FormSubmissionStep
from onegov.fedpol.layout import FormSubmissionLayout, FormSubmissionStepLayout
from onegov.fedpol.utils import get_step_form
from onegov.form import FormCollection, FormDefinition
from onegov.gis import Coordinates
from onegov.org.elements import Link
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
