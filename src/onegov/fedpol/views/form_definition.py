from __future__ import annotations

import morepath

from onegov.core.security import Public
from onegov.fedpol import _, FedpolApp
from onegov.fedpol.models import FormSubmissionStep
from onegov.fedpol.layout import FormSubmissionStepLayout
from onegov.fedpol.utils import get_step_form
from onegov.form import FormCollection, FormDefinition
from onegov.gis import Coordinates
from onegov.org.views.form_definition import get_hints
from onegov.town6.layout import FormSubmissionLayout


from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fedpol.request import FedpolRequest
    from onegov.form import Form
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


def get_form_class(self: FormDefinition, request: FedpolRequest) -> type[Form]:
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
    form=get_form_class
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

    layout = (
        FormSubmissionStepLayout if has_steps else FormSubmissionLayout
    )(self, request, title=self.title)

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
