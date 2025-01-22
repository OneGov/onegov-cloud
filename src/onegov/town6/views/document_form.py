from __future__ import annotations

from onegov.core.security.permissions import Public
from onegov.org.models.document_form import (FormDocument,
                                              FormDocumentCollection)
from onegov.org.views.document_form import (
    get_form_document_form, handle_edit_document_form_page,
    handle_new_document_form_page, view_document_form_page)
from onegov.town6 import TownApp
from onegov.core.security import Private
from onegov.town6.layout import FormDocumentLayout, FormEditorLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response
    from onegov.org.forms.document_form import DocumentForm


@TownApp.html(
    model=FormDocument,
    template='document_form_page.pt',
    permission=Public)
def town_view_document_form_page(
    self: FormDocument,
    request: TownRequest,
    layout: FormDocumentLayout | None = None
) -> RenderData | Response:
    return view_document_form_page(
        self, request, layout=FormDocumentLayout(self, request)
    )


@TownApp.form(
    model=FormDocumentCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=get_form_document_form
)
def town_handle_new_document_form(
    self: FormDocumentCollection,
    request: TownRequest,
    form: DocumentForm
) -> RenderData | Response:
    return handle_new_document_form_page(
        self, request, form, layout=FormEditorLayout(self, request)
    )


@TownApp.form(
    model=FormDocument,
    name='edit',
    template='form.pt',
    permission=Private,
    form=get_form_document_form
)
def town_handle_edit_document_form(
    self: FormDocument,
    request: TownRequest,
    form: DocumentForm
) -> RenderData | Response:
    return handle_edit_document_form_page(
        self, request, form, layout=FormEditorLayout(self, request)
    )
