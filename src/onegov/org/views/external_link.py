from __future__ import annotations

from onegov.core.elements import BackLink, Link
from onegov.org import _
from onegov.core.security import Private
from onegov.org import OrgApp
from onegov.org.forms.external_link import ExternalLinkForm
from onegov.org.layout import ExternalLinkLayout
from onegov.org.models.external_link import (
    ExternalLinkCollection, ExternalLink
)
from morepath import redirect


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.org.request import OrgRequest
    from webob import Response


def get_external_link_form(
    model: ExternalLink | ExternalLinkCollection,
    request: OrgRequest
) -> type[ExternalLinkForm]:

    if isinstance(model, ExternalLinkCollection):
        model = model.model_class()
    return model.with_content_extensions(ExternalLinkForm, request)


@OrgApp.form(
    model=ExternalLinkCollection, name='new', template='form.pt',
    permission=Private, form=get_external_link_form
)
def handle_new_external_link(
    self: ExternalLinkCollection,
    request: OrgRequest,
    form: ExternalLinkForm,
    layout: ExternalLinkLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        external_link = self.add_by_form(form)
        request.success(_('Added a new external link'))
        return redirect(request.class_link(
            ExternalLinkCollection.target(external_link)
        ))

    layout = layout or ExternalLinkLayout(self, request)
    layout.edit_mode = True
    target = self.supported_collections.get(self.type) if self.type else None
    layout.editmode_links[1] = Link(
        _('Cancel'), request.class_link(target), attrs={'class': 'cancel-link'}
    ) if target else BackLink(attrs={'class': 'cancel-link'})
    layout.breadcrumbs.append(
        Link(_('New external form'), '#'),
    )

    return {
        'layout': layout,
        'title': request.params.get('title', _('New external link')),
        'form': form,
    }


@OrgApp.form(model=ExternalLink, name='edit', template='form.pt',
             permission=Private, form=get_external_link_form)
def edit_external_link(
    self: ExternalLink,
    request: OrgRequest,
    form: ExternalLinkForm,
    layout: ExternalLinkLayout | None = None
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        to = request.params.get('to')
        if not isinstance(to, str):
            to = ''
        return redirect(to or request.link(request.app.org))

    form.process(obj=self)

    layout = layout or ExternalLinkLayout(self, request)
    layout.edit_mode = True
    links = layout.editmode_links + layout.editbar_links  # type:ignore
    layout.editmode_links = links
    layout.breadcrumbs.extend([
        Link(_('Edit external form'), '#'),
    ])

    return {
        'layout': layout,
        'title': request.params.get('title', _('Edit external link')),
        'form': form,
    }


@OrgApp.view(model=ExternalLink, permission=Private, request_method='DELETE')
def delete_external_link(self: ExternalLink, request: OrgRequest) -> None:
    request.assert_valid_csrf_token()
    request.session.delete(self)
