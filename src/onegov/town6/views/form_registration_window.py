from onegov.core.security import Private
from onegov.form import FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.org.forms.form_registration import FormRegistrationMessageForm
from onegov.org.views.form_registration_window import (
    handle_new_registration_form, view_registration_window,
    handle_edit_registration_form, view_send_form_registration_message)
from onegov.town6 import TownApp
from onegov.org.forms import FormRegistrationWindowForm
from onegov.town6.layout import FormSubmissionLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=FormDefinition,
    name='new-registration-window',
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt'
)
def town_handle_new_registration_form(
    self: FormDefinition,
    request: 'TownRequest',
    form: FormRegistrationWindowForm
) -> 'RenderData | Response':
    return handle_new_registration_form(
        self, request, form, FormSubmissionLayout(self, request))


@TownApp.form(
    model=FormRegistrationWindow,
    permission=Private,
    name='send-message',
    template='form.pt',
    form=FormRegistrationMessageForm
)
def town_view_send_form_registration_message(
    self: FormRegistrationWindow,
    request: 'TownRequest',
    form: FormRegistrationMessageForm
) -> 'RenderData | Response':
    return view_send_form_registration_message(
        self, request, form, FormSubmissionLayout(self.form, request))


@TownApp.html(
    model=FormRegistrationWindow,
    permission=Private,
    template='registration_window.pt'
)
def town_view_registration_window(
    self: FormRegistrationWindow,
    request: 'TownRequest'
) -> 'RenderData':
    return view_registration_window(
        self, request, FormSubmissionLayout(self.form, request))


@TownApp.form(
    model=FormRegistrationWindow,
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt',
    name='edit'
)
def town_handle_edit_registration_form(
    self: FormRegistrationWindow,
    request: 'TownRequest',
    form: FormRegistrationWindowForm
) -> 'RenderData | Response':
    return handle_edit_registration_form(
        self, request, form, FormSubmissionLayout(self.form, request))
