from onegov.core.security import Private, Public
from onegov.form import FormCollection, FormDefinition
from onegov.form.collection import SurveyCollection
from onegov.form.models.definition import SurveyDefinition
from onegov.org.forms.form_definition import (
    FormDefinitionUrlForm, SurveyDefinitionForm)
from onegov.org.views.form_definition import (
    get_form_class, handle_defined_survey, handle_new_definition,
    handle_edit_definition, handle_defined_form, handle_change_form_name,
    handle_new_survey_definition)
from onegov.town6 import TownApp
from onegov.town6.layout import (FormEditorLayout, FormSubmissionLayout,
                                 SurveySubmissionLayout)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.org.forms import FormDefinitionForm
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=FormDefinition,
    template='form.pt',
    permission=Public,
    form=lambda self, request: self.form_class
)
def town_handle_defined_form(
    self: FormDefinition,
    request: 'TownRequest',
    form: 'Form'
) -> 'RenderData | Response':
    return handle_defined_form(
        self, request, form, FormSubmissionLayout(self, request))


@TownApp.form(
    model=FormCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_form_class
)
def town_handle_new_definition(
    self: FormCollection,
    request: 'TownRequest',
    form: 'FormDefinitionForm'
) -> 'RenderData | Response':
    return handle_new_definition(
        self, request, form, FormEditorLayout(self, request))


@TownApp.form(
    model=FormDefinition,
    template='form.pt',
    permission=Private,
    form=get_form_class,
    name='edit'
)
def town_handle_edit_definition(
    self: FormDefinition,
    request: 'TownRequest',
    form: 'FormDefinitionForm'
) -> 'RenderData | Response':
    return handle_edit_definition(
        self, request, form, FormEditorLayout(self, request))


@TownApp.form(
    model=FormDefinition,
    form=FormDefinitionUrlForm,
    template='form.pt',
    permission=Private,
    name='change-url'
)
def town_handle_change_form_name(
    self: FormDefinition,
    request: 'TownRequest',
    form: FormDefinitionUrlForm
) -> 'RenderData | Response':
    return handle_change_form_name(
        self, request, form, FormEditorLayout(self, request))


@TownApp.form(
    model=SurveyDefinition,
    template='form.pt',
    permission=Public,
    form=lambda self, request: self.form_class
)
def town_handle_defined_survey(
    self: SurveyDefinition,
    request: 'TownRequest',
    form: 'Form'
) -> 'RenderData | Response':
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
    request: 'TownRequest',
    form: SurveyDefinitionForm
) -> 'RenderData | Response':
    return handle_new_survey_definition(
        self, request, form, FormEditorLayout(self, request))


# @TownApp.form(
#     model=SurveyDefinition,
#     template='form.pt',
#     permission=Private,
#     form=get_form_class,
#     name='edit'
# )
# def town_handle_edit_survey_definition(
#     self: SurveyDefinition,
#     request: 'TownRequest',
#     form: 'SurveyDefinitionForm'
# ) -> 'RenderData | Response':
#     return handle_edit_survey_definition(
#         self, request, form, FormEditorLayout(self, request))


# @TownApp.form(
#     model=SurveyDefinition,
#     form=SurveyDefinitionForm,
#     template='form.pt',
#     permission=Private,
#     name='change-url'
# )
# def town_handle_change_survey_name(
#     self: FormDefinition,
#     request: 'TownRequest',
#     form: FormDefinitionUrlForm
# ) -> 'RenderData | Response':
#     return handle_change_survey_name(
#         self, request, form, FormEditorLayout(self, request))
