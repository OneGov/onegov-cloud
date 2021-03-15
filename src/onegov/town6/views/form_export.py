from onegov.core.security import Private
from onegov.form import FormDefinition

from onegov.org.views.form_export import handle_form_submissions_export
from onegov.town6 import TownApp
from onegov.org.forms import FormSubmissionsExport
from onegov.town6.layout import FormSubmissionLayout


@TownApp.form(
    model=FormDefinition,
    name='export',
    permission=Private,
    form=FormSubmissionsExport,
    template='export.pt')
def town_handle_form_submissions_export(self, request, form):
    return handle_form_submissions_export(
        self, request, form, FormSubmissionLayout(self, request))
