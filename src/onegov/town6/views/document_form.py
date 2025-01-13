from onegov.form.models.document_form import DocumentFormCollection
from onegov.org.views.document_form import handle_new_document_form_page
from onegov.town6 import TownApp
from onegov.core.security import Private
from onegov.town6.layout import FormEditorLayout
from onegov.org.forms.document_form import DocumentForm


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@TownApp.form(
    model=DocumentFormCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=DocumentForm
)
def town_handle_new_document_form(
    self: DocumentFormCollection,
    request: 'TownRequest',
    form: DocumentForm
) -> 'RenderData | Response':
    return handle_new_document_form_page(
        self, request, form, layout=FormEditorLayout(self, request)
    )
