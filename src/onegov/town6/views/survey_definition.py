from __future__ import annotations

from onegov.core.security import Private, Public
from onegov.form.collection import SurveyCollection
from onegov.form.models.definition import SurveyDefinition
from onegov.org.forms.form_definition import SurveyDefinitionForm
from onegov.org.views.survey_definition import (
    handle_defined_survey, handle_edit_survey_definition,
    view_survey_results, handle_new_survey_definition)
from onegov.town6 import TownApp
from onegov.town6.layout import FormEditorLayout, SurveySubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=SurveyDefinition,
    template='form.pt',
    permission=Public,
    form=lambda self, request: self.form_class
)
def town_handle_defined_survey(
    self: SurveyDefinition,
    request: TownRequest,
    form: Form
) -> RenderData | Response:
    return handle_defined_survey(
        self, request, form, SurveySubmissionLayout(self, request))


@TownApp.form(
    model=SurveyCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=SurveyDefinitionForm
)
def town_handle_new_survey_definition(
    self: SurveyCollection,
    request: TownRequest,
    form: SurveyDefinitionForm
) -> RenderData | Response:
    return handle_new_survey_definition(
        self, request, form, FormEditorLayout(self, request))


@TownApp.form(
    model=SurveyDefinition,
    template='form.pt',
    permission=Private,
    form=SurveyDefinitionForm,
    name='edit'
)
def town_handle_edit_survey_definition(
    self: SurveyDefinition,
    request: TownRequest,
    form: SurveyDefinitionForm
) -> RenderData | Response:
    return handle_edit_survey_definition(
        self, request, form, FormEditorLayout(self, request))


@TownApp.html(model=SurveyDefinition, template='survey_results.pt',
              permission=Private, name='results')
def town_view_survey_results(
    self: SurveyDefinition,
    request: TownRequest
) -> RenderData:
    return view_survey_results(
        self, request, SurveySubmissionLayout(self, request))
