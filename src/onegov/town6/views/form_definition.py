from __future__ import annotations

from onegov.core.security import Private, Public
from onegov.form import FormCollection, FormDefinition
from onegov.org.forms.form_definition import FormDefinitionUrlForm
from onegov.org.views.form_definition import (
    get_form_class, handle_new_definition, handle_edit_definition,
    handle_defined_form, handle_change_form_name)

from onegov.town6 import TownApp
from onegov.town6.layout import FormEditorLayout, FormSubmissionLayout


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
    request: TownRequest,
    form: Form
) -> RenderData | Response:
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
