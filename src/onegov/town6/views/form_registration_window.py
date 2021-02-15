from onegov.core.security import Private
from onegov.form import FormDefinition
from onegov.form import FormRegistrationWindow
from onegov.org.views.form_registration_window import \
    handle_new_registration_form, view_registration_window, \
    handle_edit_registration_form
from onegov.town6 import TownApp, _
from onegov.org.forms import FormRegistrationWindowForm


@TownApp.form(
    model=FormDefinition,
    name='new-registration-window',
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt')
def town_handle_new_registration_form(self, request, form):
    return handle_new_registration_form(self, request, form)


@TownApp.html(
    model=FormRegistrationWindow,
    permission=Private,
    template='registration_window.pt')
def town_view_registration_window(self, request):
    return view_registration_window(self, request)


@TownApp.form(
    model=FormRegistrationWindow,
    permission=Private,
    form=FormRegistrationWindowForm,
    template='form.pt',
    name='edit')
def town_handle_edit_registration_form(self, request, form):
    return handle_edit_registration_form(self, request, form)
