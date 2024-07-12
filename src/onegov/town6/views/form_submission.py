from onegov.core.security import Public, Private
from onegov.form.models.submission import (CompleteSurveySubmission,
                                           PendingSurveySubmission)
from onegov.org.views.form_submission import (handle_pending_submission,
                                              handle_pending_survey_submission)
from onegov.form import (
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.town6 import TownApp
from onegov.town6.layout import FormSubmissionLayout, SurveySubmissionLayout


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


@TownApp.html(model=PendingSurveySubmission, template='survey_submission.pt',
              permission=Public, request_method='GET')
@TownApp.html(model=PendingSurveySubmission, template='survey_submission.pt',
              permission=Public, request_method='POST')
@TownApp.html(model=CompleteSurveySubmission, template='survey_submission.pt',
              permission=Private, request_method='GET')
@TownApp.html(model=CompleteSurveySubmission, template='survey_submission.pt',
              permission=Private, request_method='POST')
def town_handle_pending_survey_submission(
    self: PendingSurveySubmission | CompleteSurveySubmission,
    request: 'TownRequest'
) -> 'RenderData | Response':
    if 'title' in request.GET:
        title = request.GET['title']
    else:
        assert self.survey is not None
        title = self.survey.title
    return handle_pending_survey_submission(
        self, request, SurveySubmissionLayout(self, request, title))
