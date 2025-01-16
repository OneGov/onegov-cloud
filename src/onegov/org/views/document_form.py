import morepath

from onegov.core.security import Private, Public
from onegov.form import FormDefinition
from onegov.form.collection import FormCollection
from onegov.form.models.document_form import (
    FormDocumentCollection, FormDocument)
from onegov.org import _, OrgApp
from onegov.org.elements import Link
from onegov.org.forms.document_form import DocumentForm
from onegov.org.layout import FormDocumentLayout, FormEditorLayout


from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


@OrgApp.html(model=FormDocument, template='document_form_page.pt',
             permission=Public)
def view_document_form_page(
    self: FormDocument,
    request: 'OrgRequest',
    layout: FormDocumentLayout | None = None
) -> 'RenderData | Response':

    layout = layout or FormDocumentLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'page': self
        }


@OrgApp.form(
    model=FormDocumentCollection,
    name='new', template='form.pt',
    permission=Private, form=DocumentForm
)
def handle_new_document_form_page(
    self: FormDocumentCollection,
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


@OrgApp.form(
    model=FormDocument,
    name='edit', template='form.pt',
    permission=Private, form=DocumentForm
)
def handle_edit_document_form_page(
    self: FormDocument,
    request: 'OrgRequest',
    form: DocumentForm,
    layout: FormDocumentLayout | None = None
) -> 'RenderData | Response':

    if form.submitted(request):
        assert form.title.data is not None
        form.populate_obj(self)

        request.success(_('Your changes were saved'))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    layout = layout or FormDocumentLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.class_link(FormCollection)),
        Link(self.title, request.link(self)),
        Link(_('Edit'), request.link(self, name='edit')),
    ]
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': _('Edit Document Form'),
        'form': form,
    }
