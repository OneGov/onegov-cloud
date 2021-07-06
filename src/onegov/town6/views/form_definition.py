from onegov.core.security import Private, Public
from onegov.form import FormCollection, FormDefinition
from onegov.org.views.form_definition import get_form_class, \
    handle_new_definition, handle_edit_definition, handle_defined_form
from onegov.town6 import TownApp
from onegov.town6.layout import FormEditorLayout, FormSubmissionLayout


@TownApp.form(model=FormDefinition, template='form.pt', permission=Public,
              form=lambda self, request: self.form_class)
def town_handle_defined_form(self, request, form):
    return handle_defined_form(
        self, request, form, FormSubmissionLayout(self, request))


@TownApp.form(model=FormCollection, name='new', template='form.pt',
              permission=Private, form=get_form_class)
def town_handle_new_definition(self, request, form):
    return handle_new_definition(
        self, request, form, FormEditorLayout(self, request))


@TownApp.form(model=FormDefinition, template='form.pt', permission=Private,
              form=get_form_class, name='edit')
def town_handle_edit_definition(self, request, form):
    return handle_edit_definition(
        self, request, form, FormEditorLayout(self, request))
