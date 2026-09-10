from __future__ import annotations

from onegov.core.security import Private, Public
from onegov.core.templates import render_macro
from onegov.form import FormCollection, FormDefinition
from onegov.form.models.submission import FormSubmission
from onegov.org.forms.form_definition import FormDefinitionUrlForm
from onegov.org.views.form_definition import (
    get_form_class, handle_new_definition, handle_edit_definition,
    handle_change_form_name, handle_defined_form)

from onegov.town6 import TownApp
from onegov.town6.layout import FormEditorLayout, FormSubmissionLayout
from webob import Response


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.org.forms import FormDefinitionForm
    from onegov.town6.request import TownRequest


@TownApp.form(
    model=FormDefinition,
    template='form_definition.pt',
    permission=Public,
    form=lambda self, request: self.form_class
)
def town_handle_defined_form(
    self: FormDefinition,
    request: TownRequest,
    form: Form
) -> RenderData | Response:

    return request.redirect(
        request.class_link(
            FormCollection,
            query_params={'form': self.name}
        ))


@TownApp.form(
    model=FormDefinition,
    permission=Public,
    form=lambda self, request: self.form_class,
    name='modal'
)
def view_form_modal(
    self: FormDefinition,
    request: TownRequest,
    form: Form,
    layout: FormSubmissionLayout | None = None
) -> str | Response:
    result = handle_defined_form(self, request, form, layout)
    if isinstance(result, Response):
        return result
    result['full_page_width'] = True
    result['layout'] = FormSubmissionLayout(self, request)
    return render_macro(
        result['layout'].macros['form-modal-definition'], request, result)


@TownApp.form(
    model=FormCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_form_class
)
def town_handle_new_definition(
    self: FormCollection,
    request: TownRequest,
    form: FormDefinitionForm
) -> RenderData | Response:
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
    request: TownRequest,
    form: FormDefinitionForm
) -> RenderData | Response:
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
    request: TownRequest,
    form: FormDefinitionUrlForm
) -> RenderData | Response:
    return handle_change_form_name(
        self, request, form, FormEditorLayout(self, request))
