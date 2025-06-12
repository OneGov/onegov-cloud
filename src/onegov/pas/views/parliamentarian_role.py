from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import ParliamentarianRoleCollection
from onegov.pas.forms import ParliamentarianRoleForm
from onegov.pas.layouts import ParliamentarianRoleLayout
from onegov.parliament.models import ParliamentarianRole

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=ParliamentarianRole,
    template='parliamentarian_role.pt',
    permission=Private
)
def view_parliamentarian_role(
    self: ParliamentarianRole,
    request: TownRequest
) -> RenderData:

    layout = ParliamentarianRoleLayout(self, request)

    return {
        'layout': layout,
        'parliamentarian_role': self,
        'title': layout.title,
    }


@PasApp.form(
    model=ParliamentarianRole,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentarianRoleForm
)
def edit_parliamentarian_role(
    self: ParliamentarianRole,
    request: TownRequest,
    form: ParliamentarianRoleForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self.parliamentarian))

    form.process(obj=self)

    layout = ParliamentarianRoleLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=ParliamentarianRole,
    request_method='DELETE',
    permission=Private
)
def delete_parliamentarian_role(
    self: ParliamentarianRole,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = ParliamentarianRoleCollection(request.session)
    collection.delete(self)
