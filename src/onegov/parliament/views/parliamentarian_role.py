from __future__ import annotations

from onegov.core.elements import Link
from onegov.parliament import _
from onegov.parliament.collections import ParliamentarianRoleCollection

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob import Response

    from onegov.core.types import RenderData
    from onegov.parliament.forms import ParliamentarianRoleForm
    from onegov.parliament.models import ParliamentarianRole
    from onegov.pas.layouts import PASParliamentarianRoleLayout
    from onegov.town6.request import TownRequest


def view_parliamentarian_role(
    self: ParliamentarianRole,
    request: TownRequest,
    layout: PASParliamentarianRoleLayout
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
    layout: PASParliamentarianRoleLayout
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self.parliamentarian))

    form.process(obj=self)

    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

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
