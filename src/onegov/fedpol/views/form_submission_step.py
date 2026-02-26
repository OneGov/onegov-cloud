from __future__ import annotations

import morepath

from onegov.core.security import Public
from onegov.fedpol import _, FedpolApp
from onegov.fedpol.layout import FormSubmissionStepLayout
from onegov.fedpol.models import FormSubmissionStep
from onegov.fedpol.utils import get_step_form
from onegov.form import FormCollection, FormDefinition


from typing import TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fedpol.request import FedpolRequest
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


@FedpolApp.html(
    model=FormSubmissionStep,
    template='form.pt',
    permission=Public,
    request_method='GET'
)
@FedpolApp.html(
    model=FormSubmissionStep,
    template='form.pt',
    permission=Public,
    request_method='POST'
)
def handle_pending_submission(
    self: FormSubmissionStep,
    request: FedpolRequest
) -> RenderData | Response:

    form_class = get_step_form(self.submission, self.step)
    if form_class is None:
        return morepath.redirect(request.link(self.submission))

    form = request.get_form(form_class, data=self.submission.data)
    form.action = request.link(self)
    form.model = self.submission

    collection = FormCollection(request.session)
    if form.submitted(request):
        collection.submissions.update(self.submission, form, partial=True)
        return morepath.redirect(
            request.link(self.next_step or self.submission)
        )
    elif not request.POST and request.GET.get('submitted') == '1':
        form.validate()

    assert self.submission.form is not None
    if hasattr(form, 'step_name'):
        title = self.submission.form.title
        step_title = form.step_name
    else:
        title = self.submission.form.title
        step_title = None

    return {
        'layout': FormSubmissionStepLayout(self, request, title, step_title),
        'title': step_title or title,
        'form': form,
        'button_text': _('Continue')
    }
