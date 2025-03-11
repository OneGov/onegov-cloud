from __future__ import annotations

from onegov.core.security import Public, Private
from onegov.form.models.submission import SurveySubmission
from onegov.org.models.ticket import (
    DirectoryEntryTicket,
    FormSubmissionTicket,
    ReservationTicket,
)
from onegov.org.views.form_submission import (
    handle_edit_submission_from_ticket,
    handle_pending_submission,
    handle_survey_submission
)
from onegov.form import (
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.town6 import TownApp
from onegov.town6.layout import (
    FormSubmissionLayout,
    SurveySubmissionLayout,
    TicketLayout,
)


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
    request: TownRequest
) -> RenderData | Response:
    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.form is not None
        title = self.form.title
    return handle_pending_submission(
        self, request, FormSubmissionLayout(self, request, title))


@TownApp.html(model=DirectoryEntryTicket, template='submission.pt',
             permission=Private, request_method='GET', name='submission')
@TownApp.html(model=DirectoryEntryTicket, template='submission.pt',
             permission=Private, request_method='POST', name='submission')
@TownApp.html(model=FormSubmissionTicket, template='submission.pt',
             permission=Private, request_method='GET', name='submission')
@TownApp.html(model=FormSubmissionTicket, template='submission.pt',
             permission=Private, request_method='POST', name='submission')
@TownApp.html(model=ReservationTicket, template='submission.pt',
             permission=Private, request_method='GET', name='submission')
@TownApp.html(model=ReservationTicket, template='submission.pt',
             permission=Private, request_method='POST', name='submission')
def town_handle_edit_submission_from_ticket(
    self: FormSubmissionTicket | ReservationTicket,
    request: TownRequest,
    layout: TicketLayout | None = None
) -> RenderData | Response:
    return handle_edit_submission_from_ticket(
        self, request, TicketLayout(self, request))


@TownApp.html(model=SurveySubmission, template='survey_submission.pt',
              permission=Public, request_method='GET')
@TownApp.html(model=SurveySubmission, template='survey_submission.pt',
              permission=Public, request_method='POST')
def town_handle_survey_submission(
    self: SurveySubmission,
    request: TownRequest
) -> RenderData | Response:
    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.survey is not None
        title = self.survey.title
    return handle_survey_submission(
        self, request, SurveySubmissionLayout(self, request, title))
