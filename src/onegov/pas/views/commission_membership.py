from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.org.forms.commission_membership import CommissionMembershipForm
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import PASCommissionMembershipCollection
from onegov.pas.layouts import PASCommissionMembershipLayout
from onegov.pas.models import PASCommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASCommissionMembership,
    template='commission_membership.pt',
    permission=Private
)
def view_commission_membership(
    self: PASCommissionMembership,
    request: TownRequest
) -> RenderData:

    layout = PASCommissionMembershipLayout(self, request)

    return {
        'layout': layout,
        'commission_membership': self,
        'title': layout.title,
    }


@PasApp.form(
    model=PASCommissionMembership,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CommissionMembershipForm
)
def edit_commission_membership(
    self: PASCommissionMembership,
    request: TownRequest,
    form: CommissionMembershipForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self.commission))

    form.process(obj=self)

    layout = PASCommissionMembershipLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=PASCommissionMembership,
    request_method='DELETE',
    permission=Private
)
def delete_commission_membership(
    self: PASCommissionMembership,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = PASCommissionMembershipCollection(request.session)
    collection.delete(self)
