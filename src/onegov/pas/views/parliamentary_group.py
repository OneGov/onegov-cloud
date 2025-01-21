from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import ParliamentaryGroupCollection
from onegov.pas.forms import ParliamentaryGroupForm
from onegov.pas.layouts import ParliamentaryGroupCollectionLayout
from onegov.pas.layouts import ParliamentaryGroupLayout
from onegov.pas.models import ParliamentaryGroup

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=ParliamentaryGroupCollection,
    template='parliamentary_groups.pt',
    permission=Private
)
def view_parliamentary_groups(
    self: ParliamentaryGroupCollection,
    request: TownRequest
) -> RenderData:

    layout = ParliamentaryGroupCollectionLayout(self, request)

    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value))
        ) for title, value in (
            (_('Active'), True),
            (_('Inactive'), False)
        )
    ]

    return {
        'add_link': request.link(self, name='new'),
        'filters': filters,
        'layout': layout,
        'parliamentary_groups': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=ParliamentaryGroupCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def add_parliamentary_group(
    self: ParliamentaryGroupCollection,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    if form.submitted(request):
        parliamentary_group = self.add(**form.get_useful_data())
        request.success(_('Added a new parliamentary group'))

        return request.redirect(request.link(parliamentary_group))

    layout = ParliamentaryGroupCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New parliamentary group'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=ParliamentaryGroup,
    template='parliamentary_group.pt',
    permission=Private
)
def view_parliamentary_group(
    self: ParliamentaryGroup,
    request: TownRequest
) -> RenderData:

    layout = ParliamentaryGroupLayout(self, request)

    return {
        'layout': layout,
        'parliamentary_group': self,
        'title': layout.title,
    }


@PasApp.form(
    model=ParliamentaryGroup,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentaryGroupForm
)
def edit_parliamentary_group(
    self: ParliamentaryGroup,
    request: TownRequest,
    form: ParliamentaryGroupForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = ParliamentaryGroupLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []
    layout.include_editor()

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=ParliamentaryGroup,
    request_method='DELETE',
    permission=Private
)
def delete_parliamentary_group(
    self: ParliamentaryGroup,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = ParliamentaryGroupCollection(request.session)
    collection.delete(self)
