from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import CommissionMembershipCollection
from onegov.pas.forms import CommissionMembershipForm
from onegov.pas.layouts import CommissionMembershipLayout
from onegov.pas.models import CommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=CommissionMembership,
    template='commission_membership.pt',
    permission=Private
)
def view_commission_membership(
    self: CommissionMembership,
    request: 'TownRequest'
) -> 'RenderData':

    layout = CommissionMembershipLayout(self, request)

    return {
        'layout': layout,
        'commission_membership': self,
        'title': layout.title,
    }


@PasApp.form(
    model=CommissionMembership,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CommissionMembershipForm
)
def edit_commission_membership(
    self: CommissionMembership,
    request: 'TownRequest',
    form: CommissionMembershipForm
) -> 'RenderData | Response':

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_("Your changes were saved"))
        return request.redirect(request.link(self.commission))

    form.process(obj=self)

    layout = CommissionMembershipLayout(self, request)
    layout.breadcrumbs.append(Link(_("Edit"), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }


@PasApp.view(
    model=CommissionMembership,
    request_method='DELETE',
    permission=Private
)
def delete_commission_membership(
    self: CommissionMembership,
    request: 'TownRequest'
) -> None:

    request.assert_valid_csrf_token()

    collection = CommissionMembershipCollection(request.session)
    collection.delete(self)
