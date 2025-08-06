from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private, Public
from onegov.org.forms.commission_membership import CommissionMembershipForm
from onegov.org.models import RISCommissionMembership
from onegov.parliament.models import CommissionMembership
from onegov.town6 import _
from onegov.town6 import TownApp
from onegov.town6.layout import RISCommissionMembershipLayout
from onegov.town6.request import TownRequest

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from webob.response import Response

    from onegov.core.types import RenderData


@TownApp.html(
    model=CommissionMembership,
    template='commission_membership.pt',
    permission=Private
)
def view_commission_membership(
    self: RISCommissionMembership,
    request: TownRequest
) -> RenderData | Response:

    layout = RISCommissionMembershipLayout(self, request)

    return {
        'layout': layout,
        'commission_membership': self,
        'title': layout.title,
    }


@TownApp.form(
    model=CommissionMembership,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CommissionMembershipForm
)
def edit_commission_membership(
    self: CommissionMembership,
    request: TownRequest,
    form: CommissionMembershipForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self.commission))

    form.process(obj=self)

    layout = RISCommissionMembershipLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.editbar_links = []

    return {
        'layout': layout,
        'title': layout.title,
        'form': form,
        'form_width': 'large'
    }
