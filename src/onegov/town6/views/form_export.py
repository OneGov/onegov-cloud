from __future__ import annotations

from onegov.core.security import Private
from onegov.form import FormDefinition

from onegov.org.views.form_export import handle_form_submissions_export
from onegov.town6 import TownApp
from onegov.org.forms import FormSubmissionsExport
from onegov.town6.layout import FormSubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=FormDefinition,
    name='export',
    permission=Private,
    form=FormSubmissionsExport,
    template='export.pt'
)
def town_handle_form_submissions_export(
    self: FormDefinition,
    request: TownRequest,
    form: FormSubmissionsExport
) -> RenderData | Response:
    return handle_form_submissions_export(
        self, request, form, FormSubmissionLayout(self, request))
