from __future__ import annotations

from onegov.core.security import Private
from onegov.form.models.definition import SurveyDefinition
from onegov.org.forms.survey_export import SurveySubmissionsExport
from onegov.org.views.survey_export import (
    handle_form_submissions_export)
from onegov.town6 import TownApp
from onegov.town6.layout import SurveySubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=SurveyDefinition,
    name='export',
    template='form.pt',
    permission=Private,
    form=SurveySubmissionsExport
)
def town_handle_form_submissions_export(
    self: SurveyDefinition,
    request: TownRequest,
    form: SurveySubmissionsExport
) -> RenderData | Response:
    return handle_form_submissions_export(
        self, request, form, SurveySubmissionLayout(self, request))
