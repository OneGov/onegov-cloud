from __future__ import annotations

from onegov.core.security import Private
from onegov.pas import PasApp
from onegov.core.elements import Link
from onegov.pas import _
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.forms import PASParliamentarianForm
from onegov.pas.forms import PASParliamentarianRoleForm
from onegov.pas.layouts import PASParliamentarianCollectionLayout
from onegov.pas.layouts import PASParliamentarianLayout
from onegov.pas.models import PASParliamentarian
from onegov.town6.views.parliamentarian import (
    add_parliamentary_group_membership)
from onegov.town6.views.parliamentarian import add_parliamentarian
from onegov.town6.views.parliamentarian import view_parliamentarian
from onegov.town6.views.parliamentarian import view_parliamentarians


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASParliamentarianCollection,
    template='parliamentarians.pt',
    permission=Private
)
def pas_view_parliamentarians(
    self: PASParliamentarianCollection,
    request: TownRequest
) -> RenderData | Response:
    layout = PASParliamentarianCollectionLayout(self, request)
    return view_parliamentarians(self, request, layout)


@PasApp.form(
    model=PASParliamentarianCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=PASParliamentarianForm
)
def pas_add_parliamentarian(
    self: PASParliamentarianCollection,
    request: TownRequest,
    form: PASParliamentarianForm
) -> RenderData | Response:
    layout = PASParliamentarianCollectionLayout(self, request)
    return add_parliamentarian(self, request, form, layout)


@PasApp.html(
    model=PASParliamentarian,
    template='parliamentarian.pt',
    permission=Private
)
def pas_view_parliamentarian(
    self: PASParliamentarian,
    request: TownRequest
) -> RenderData | Response:
    layout = PASParliamentarianLayout(self, request)
    return view_parliamentarian(self, request, layout)


@PasApp.form(
    model=PASParliamentarian,
    name='edit',
    template='form.pt',
    permission=Private,
    form=PASParliamentarianForm
)
def pas_edit_parliamentarian(
    self: PASParliamentarian,
    request: TownRequest,
    form: PASParliamentarianForm
) -> RenderData | Response:

    layout = PASParliamentarianLayout(self, request)

    if form.submitted(request):
        # NOTE: Same pattern used as in edit translator
        form.update_model(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))
    elif not request.POST:
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


@PasApp.view(
    model=PASParliamentarian,
    request_method='DELETE',
    permission=Private
)
def pas_delete_parliamentarian(
    self: PASParliamentarian,
    request: TownRequest
) -> None:
    from onegov.org.models import PoliticalBusinessParticipationCollection
    from onegov.pas import _

    request.assert_valid_csrf_token()

    businesses = PoliticalBusinessParticipationCollection(request.session)
    businesses.by_parliamentarian_id(self.id).delete()

    parliamentarians = PASParliamentarianCollection(request.app)
    parliamentarians.delete(self)

    request.success(_('The parliamentarian has been deleted.'))


@PasApp.form(
    model=PASParliamentarian,
    name='new-role',
    template='form.pt',
    permission=Private,
    form=PASParliamentarianRoleForm
)
def pas_add_commission_membership(
    self: PASParliamentarian,
    request: TownRequest,
    form: PASParliamentarianRoleForm
) -> RenderData | Response:

    layout = PASParliamentarianLayout(self, request)
    return add_parliamentary_group_membership(self, request, form, layout)
