import morepath

from onegov.core.security import Private, Public
from onegov.form import FormDefinition
from onegov.form.collection import FormCollection
from onegov.form.models.document_form import (
    DocumentFormCollection, DocumentFormPage)
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms.document_form import DocumentForm
from onegov.org.layout import FormEditorLayout, PageLayout


from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


@OrgApp.html(model=DocumentFormPage, template='topic.pt', permission=Public)
def view_document_form_page(
    self: DocumentFormPage,
    request: 'OrgRequest',
    layout: PageLayout | None = None
) -> 'RenderData | Response':

    layout = layout or PageLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
    }


@OrgApp.form(
    model=DocumentFormCollection,
    name='new', template='form.pt',
    permission=Private, form=DocumentForm
)
def handle_new_document_form_page(
    self: DocumentFormCollection,
    request: 'OrgRequest',
    form: DocumentForm,
    layout: FormEditorLayout | None = None
) -> 'RenderData | Response':

    if form.submitted(request):
        assert form.title.data is not None
        document_form = self.add_by_form(form)

        request.success(_('Added a new form'))
        return morepath.redirect(request.link(document_form))

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.class_link(FormCollection)),
        Link(_('New Document Form'), request.link(self, name='new'))
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('New Document Form'),
        'form': form,
        'form_width': 'large',
    }
