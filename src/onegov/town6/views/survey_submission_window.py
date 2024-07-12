from onegov.core.security import Private
from onegov.form import SurveyDefinition
from onegov.form import SurveySubmissionWindow
from onegov.org.views.survey_submission_window import (
    handle_new_submision_form, view_submission_window,
    handle_edit_submission_window)
from onegov.town6 import TownApp
from onegov.org.forms import SurveySubmissionWindowForm
from onegov.town6.layout import SurveySubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=SurveyDefinition,
    name='new-submission-window',
    permission=Private,
    form=SurveySubmissionWindowForm,
    template='form.pt'
)
def town_handle_new_submission_form(
    self: SurveyDefinition,
    request: 'TownRequest',
    form: SurveySubmissionWindowForm
) -> 'RenderData | Response':
    return handle_new_submision_form(
        self, request, form, SurveySubmissionLayout(self, request))


@TownApp.html(
    model=SurveySubmissionWindow,
    permission=Private,
    template='submission_window.pt'
)
def town_view_submission_window(
    self: SurveySubmissionWindow,
    request: 'TownRequest'
) -> 'RenderData':
    return view_submission_window(
        self, request, SurveySubmissionLayout(self.survey, request))


@TownApp.form(
    model=SurveySubmissionWindow,
    permission=Private,
    form=SurveySubmissionWindowForm,
    template='form.pt',
    name='edit'
)
def town_handle_edit_submission_form(
    self: SurveySubmissionWindow,
    request: 'TownRequest',
    form: SurveySubmissionWindowForm
) -> 'RenderData | Response':
    return handle_edit_submission_window(
        self, request, form, SurveySubmissionLayout(self.survey, request))
