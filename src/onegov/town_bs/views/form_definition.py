
from __future__ import annotations

import morepath

from onegov.core.security import Public
from onegov.core.templates import render_macro
from onegov.form import FormCollection, FormDefinition
from onegov.org.views.form_definition import (
    get_hints)
from onegov.town6 import _

from onegov.town_bs import TownBsApp
from onegov.town6.layout import FormSubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.town6.request import TownRequest


@TownBsApp.form(
    model=FormDefinition,
    template='form_definition.pt',
    permission=Public,
    form=lambda self, request: self.form_class
)
def town_handle_defined_form(
    self: FormDefinition,
    request: TownRequest,
    form: Form
) -> RenderData | Response:

    return request.redirect(
        request.class_link(
            FormCollection,
            query_params={'form': self.name}
        ))


@TownBsApp.form(
    model=FormDefinition,
    permission=Public,
    form=lambda self, request: self.form_class,
    name='modal'
)
def view_form_modal(
    self: FormDefinition,
    request: TownRequest,
    form: Form,
    layout: FormSubmissionLayout | None = None
) -> str | Response:
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

        return morepath.redirect(request.link(submission, 'modal'))

    layout = layout or FormSubmissionLayout(self, request)

    result = {
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
        'hints': tuple(get_hints(layout, self.current_registration_window)),
        'hints_callout': not enabled,
        'button_text': _('Continue')
    }

    result['layout'] = FormSubmissionLayout(self, request)
    return render_macro(
        layout.macros['form-modal-definition'], request, result)
