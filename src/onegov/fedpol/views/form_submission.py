from __future__ import annotations

from onegov.core.security import Public
from onegov.org.views.form_submission import handle_pending_submission
from onegov.fedpol import FedpolApp
from onegov.fedpol.layout import FormSubmissionStepLayout
from onegov.form import PendingFormSubmission
from onegov.town6.layout import FormSubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.fedpol.request import FedpolRequest
    from webob import Response


@FedpolApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='GET')
@FedpolApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='POST')
def fedpol_handle_pending_submission(
    self: PendingFormSubmission,
    request: FedpolRequest
) -> RenderData | Response:
    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.form is not None
        title = self.form.title

    # HACK: Cheap way to count fieldsets, not reliable
    num_steps = 1 if request.is_manager else sum(
        1
        for line in self.definition.splitlines()
        if line.lstrip().startswith('#')
    )

    layout = (
        FormSubmissionStepLayout if num_steps > 1 else FormSubmissionLayout
    )(self, request, title)
    return handle_pending_submission(self, request, layout)  # type: ignore[arg-type]
