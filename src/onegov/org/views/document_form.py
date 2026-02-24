from __future__ import annotations
import morepath

from onegov.core.security import Private, Public
from onegov.core.utils import normalize_for_url
from onegov.form import FormDefinition
from onegov.form.collection import FormCollection
from onegov.gis import Coordinates
from onegov.org.models.document_form import (
    FormDocumentCollection, FormDocument)
from onegov.org import _, OrgApp
from onegov.core.elements import Link
from onegov.org.forms.document_form import DocumentForm
from onegov.org.layout import FormDocumentLayout, FormEditorLayout


from typing import TypeVar, TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response

    FormDefinitionT = TypeVar('FormDefinitionT', bound=FormDefinition)


def get_form_document_form(
    model: FormDocument | FormDocumentCollection,
    request: OrgRequest
) -> type[DocumentForm]:

    if isinstance(model, FormDocumentCollection):
        model = model.model_class()
    return model.with_content_extensions(DocumentForm, request)


@OrgApp.html(model=FormDocument, template='document_form_page.pt',
             permission=Public)
def view_document_form_page(
    self: FormDocument,
    request: OrgRequest,
    layout: FormDocumentLayout | None = None
) -> RenderData | Response:

    layout = layout or FormDocumentLayout(self, request)

    return {
        'layout': layout,
        'title': self.title,
        'page': self,
        'text': self.text,
        'people': getattr(self, 'people', None),
        'files': getattr(self, 'files', None),
        'contact': getattr(self, 'contact_html', None),
        'coordinates': getattr(self, 'coordinates', Coordinates()),
        'lead': self.lead,
        'pdf': self.pdf,
        }


@OrgApp.form(
    model=FormDocumentCollection,
    name='new', template='form.pt',
    permission=Private, form=get_form_document_form
)
def handle_new_document_form_page(
    self: FormDocumentCollection,
    request: OrgRequest,
    form: DocumentForm,
    layout: FormEditorLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        assert form.title.data is not None
        if self.by_name(normalize_for_url(form.title.data)):
            request.alert(_('A form with this name already exists'))
        else:
            document_form = self.add(
                name=normalize_for_url(form.title.data),
                title=form.title.data,
            )
            form.populate_obj(document_form)
            request.success(_('Added a new form'))
            return morepath.redirect(request.link(document_form))

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.class_link(FormCollection)),
        Link(_('New Document Form'), request.link(self, name='new'))
    ]
    layout.edit_mode = True
    layout.editmode_links[1] = Link(
        text=_('Cancel'),
        url=request.class_link(FormCollection),
        attrs={'class': 'cancel-link'}
    )

    return {
        'layout': layout,
        'title': _('New Document Form'),
        'form': form,
        'form_width': 'large',
    }


@OrgApp.form(
    model=FormDocument,
    name='edit', template='form.pt',
    permission=Private, form=get_form_document_form
)
def handle_edit_document_form_page(
    self: FormDocument,
    request: OrgRequest,
    form: DocumentForm,
    layout: FormEditorLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        assert form.title.data is not None
        form.populate_obj(self)

        request.success(_('Your changes were saved'))
        return morepath.redirect(request.link(self))
    elif not request.POST:
        form.process(obj=self)

    layout = layout or FormEditorLayout(self, request)
    layout.breadcrumbs = [
        Link(_('Homepage'), layout.homepage_url),
        Link(_('Forms'), request.class_link(FormCollection)),
        Link(self.title, request.link(self)),
        Link(_('Edit'), request.link(self, name='edit')),
    ]
    layout.edit_mode = True
    layout.editmode_links[1] = Link(
        text=_('Cancel'),
        url=request.class_link(FormCollection),
        attrs={'class': 'cancel-link'}
    )

    return {
        'layout': layout,
        'title': _('Edit Document Form'),
        'form': form,
    }


@OrgApp.view(model=FormDocument, permission=Private, request_method='DELETE')
def delete_form_document(self: FormDocument, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    request.session.delete(self)
