from __future__ import annotations

from onegov.core.elements import Link
from onegov.org.forms import ParliamentarianRoleForm
from onegov.org.security import Private, Public
from onegov.org.models import RISParliamentarianRole
from onegov.parliament.collections import ParliamentarianRoleCollection
from onegov.town6 import _
from onegov.town6.app import TownApp
from onegov.town6.layout import RISParliamentarianRoleLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.response import Response

    from onegov.core.types import RenderData
    from onegov.parliament.models import ParliamentarianRole
    from onegov.pas.layouts import PASParliamentarianRoleLayout
    from onegov.town6.request import TownRequest


def view_parliamentarian_role(
    self: ParliamentarianRole,
    request: TownRequest,
    layout: PASParliamentarianRoleLayout | RISParliamentarianRoleLayout
) -> RenderData | Response:

    return {
        'layout': layout,
        'parliamentarian_role': self,
        'title': layout.title,
    }


def edit_parliamentarian_role(
    self: ParliamentarianRole,
    request: TownRequest,
    form: ParliamentarianRoleForm,
    layout: PASParliamentarianRoleLayout | RISParliamentarianRoleLayout
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self.parliamentarian))

    form.process(obj=self)

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []
    layout.edit_mode = True

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


def delete_parliamentarian_role(
    self: ParliamentarianRole,
    request: TownRequest,
) -> None:

    request.assert_valid_csrf_token()

    collection = ParliamentarianRoleCollection(request.session)
    collection.delete(self)

    request.success(_('The parliamentarian role has been deleted.'))


@TownApp.html(
    model=RISParliamentarianRole,
    template='parliamentarian_role.pt',
    permission=Public
)
def ris_view_parliamentarian_role(
    self: RISParliamentarianRole,
    request: TownRequest
) -> RenderData | Response:

    layout = RISParliamentarianRoleLayout(self, request)
    return view_parliamentarian_role(self, request, layout)


@TownApp.form(
    model=RISParliamentarianRole,
    name='edit',
    template='form.pt',
    permission=Private,
    form=ParliamentarianRoleForm
)
def ris_edit_parliamentarian_role(
    self: RISParliamentarianRole,
    request: TownRequest,
    form: ParliamentarianRoleForm
) -> RenderData | Response:

    layout = RISParliamentarianRoleLayout(self, request)
    layout.edit_mode = True
    return edit_parliamentarian_role(self, request, form, layout)


@TownApp.view(
    model=RISParliamentarianRole,
    request_method='DELETE',
    permission=Private
)
def ris_delete_parliamentarian_role(
    self: RISParliamentarianRole,
    request: TownRequest
) -> None:

    return delete_parliamentarian_role(self, request)
