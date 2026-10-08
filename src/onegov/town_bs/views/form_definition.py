from __future__ import annotations

from onegov.core.security import Public
from onegov.core.templates import render_macro
from onegov.form import FormCollection, FormDefinition
from onegov.org.views.form_definition import (
    handle_defined_form)

from onegov.town_bs import TownBsApp
from onegov.town6.layout import FormSubmissionLayout
from webob import Response


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.form import Form
    from onegov.town6.request import TownRequest


@TownBsApp.form(
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


@TownBsApp.form(
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
