from onegov.core.security import Public, Private
from onegov.org.views.form_submission import handle_defined_form, \
    handle_pending_submission, handle_complete_submission
from onegov.form import (
    FormDefinition,
    PendingFormSubmission,
    CompleteFormSubmission
)
from onegov.town6 import TownApp


@TownApp.form(model=FormDefinition, template='form.pt', permission=Public,
              form=lambda self, request: self.form_class)
def town_handle_defined_form(self, request, form):
    return handle_defined_form(self, request, form)


@TownApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='GET')
@TownApp.html(model=PendingFormSubmission, template='submission.pt',
              permission=Public, request_method='POST')
@TownApp.html(model=CompleteFormSubmission, template='submission.pt',
              permission=Private, request_method='GET')
@TownApp.html(model=CompleteFormSubmission, template='submission.pt',
              permission=Private, request_method='POST')
def town_handle_pending_submission(self, request):
    return handle_pending_submission(self, request)


@TownApp.view(model=PendingFormSubmission, name='complete',
              permission=Public, request_method='POST')
@TownApp.view(model=CompleteFormSubmission, name='complete',
              permission=Private, request_method='POST')
def town_handle_complete_submission(self, request):
    return handle_complete_submission(self, request)
