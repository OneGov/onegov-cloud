from onegov.core.security import Public, Private
from onegov.org.views.form_submission import handle_pending_submission
from onegov.form import (
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.town6 import TownApp
from onegov.town6.layout import FormSubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='GET')
@TownApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='POST')
@TownApp.html(model=CompleteFormSubmission, template='submission.pt',
              permission=Private, request_method='GET')
@TownApp.html(model=CompleteFormSubmission, template='submission.pt',
              permission=Private, request_method='POST')
def town_handle_pending_submission(
    self: PendingFormSubmission | CompleteFormSubmission,
    request: 'TownRequest'
) -> 'RenderData | Response':
    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.form is not None
        title = self.form.title
    return handle_pending_submission(
        self, request, FormSubmissionLayout(self, request, title))
