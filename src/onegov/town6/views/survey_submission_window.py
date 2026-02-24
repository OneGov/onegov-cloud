from __future__ import annotations

from onegov.core.security import Private
from onegov.core.security import Public
from onegov.form import SurveyDefinition
from onegov.form import SurveySubmissionWindow
from onegov.org.views.survey_submission_window import (
    handle_new_submission_form, view_submission_window_results,
    handle_edit_submission_window, view_submission_window_survey)
from onegov.town6 import TownApp
from onegov.org.forms import SurveySubmissionWindowForm
from onegov.town6.layout import (SurveySubmissionLayout,
                                 SurveySubmissionWindowLayout)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.form import Form
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
    request: TownRequest,
    form: SurveySubmissionWindowForm
) -> RenderData | Response:
    return handle_new_submission_form(
        self, request, form, SurveySubmissionLayout(self, request))


@TownApp.form(
    model=SurveySubmissionWindow,
    permission=Public,
    template='form.pt',
    form=lambda self, request: self.survey.form_class
)
def town_view_submission_window_survey(
    self: SurveySubmissionWindow,
    request: TownRequest,
    form: Form
) -> RenderData | Response:
    return view_submission_window_survey(
        self, request, form, SurveySubmissionWindowLayout(self, request))


@TownApp.html(
    model=SurveySubmissionWindow,
    permission=Public,
    template='submission_window.pt',
    name='results'
)
def town_view_submission_window_results(
    self: SurveySubmissionWindow,
    request: TownRequest
) -> RenderData:
    return view_submission_window_results(
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
    request: TownRequest,
    form: SurveySubmissionWindowForm
) -> RenderData | Response:
    return handle_edit_submission_window(
        self, request, form, SurveySubmissionLayout(self.survey, request))
