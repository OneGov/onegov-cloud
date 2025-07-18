from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.town6.views.commission import (
    view_commissions,
    add_commission,
    edit_commission,
    delete_commission
)
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.forms import AttendenceAddCommissionForm
from onegov.pas.forms import CommissionMembershipAddForm
from onegov.pas.forms import CommissionForm
from onegov.pas.layouts import PASCommissionCollectionLayout
from onegov.pas.layouts import PASCommissionLayout
from onegov.pas.models import Change
from onegov.pas.models import PASCommission
from onegov.pas.models import PASCommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASCommissionCollection,
    template='commissions.pt',
    permission=Private
)
def pas_view_commissions(
    self: PASCommissionCollection,
    request: TownRequest
) -> RenderData | Response:
    return view_commissions(
        self, request, PASCommissionCollectionLayout(self, request))


@PasApp.form(
    model=PASCommissionCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=CommissionForm
)
def pas_add_commission(
    self: PASCommissionCollection,
    request: TownRequest,
    form: CommissionForm
) -> RenderData | Response:
    return add_commission(
        self, request, form, PASCommissionCollectionLayout(self, request))


@PasApp.html(
    model=PASCommission,
    template='commission.pt',
    permission=Private
)
def pas_view_commission(
    self: PASCommission,
    request: TownRequest
) -> RenderData:

    layout = PASCommissionLayout(self, request)

    return {
        'layout': layout,
        'commission': self,
        'title': layout.title,
    }


@PasApp.form(
    model=PASCommission,
    name='edit',
    template='form.pt',
    permission=Private,
    form=CommissionForm
)
def pas_edit_commission(
    self: PASCommission,
    request: TownRequest,
    form: CommissionForm
) -> RenderData | Response:
    return edit_commission(
        self, request, form, PASCommissionLayout(self, request))


@PasApp.view(
    model=PASCommission,
    request_method='DELETE',
    permission=Private
)
def pas_delete_commission(
    self: PASCommission,
    request: TownRequest
) -> None:
    return delete_commission(self, request)


@PasApp.form(
    model=PASCommission,
    name='new-membership',
    template='form.pt',
    permission=Private,
    form=CommissionMembershipAddForm
)
def pas_add_commission_membership(
    self: PASCommission,
    request: TownRequest,
    form: CommissionMembershipAddForm
) -> RenderData | Response:

    if form.submitted(request):
        self.memberships.append(
            PASCommissionMembership(**form.get_useful_data())
        )
        request.success(_('Added a new parliamentarian'))
        return request.redirect(request.link(self))

    layout = PASCommissionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New parliamentarian'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New parliamentarian'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.form(
    model=PASCommission,
    name='add-attendence',
    template='form.pt',
    permission=Private,
    form=AttendenceAddCommissionForm
)
def pas_add_plenary_attendence(
    self: PASCommission,
    request: TownRequest,
    form: AttendenceAddCommissionForm
) -> RenderData | Response:

    if form.submitted(request):
        data = form.get_useful_data()
        parliamentarian_ids = data.pop('parliamentarian_id')
        collection = AttendenceCollection(request.session)
        for parliamentarian_id in parliamentarian_ids:
            attendence = collection.add(
                parliamentarian_id=parliamentarian_id,
                **data
            )
            Change.add(request, 'add', attendence)
        request.success(_('Added commission meeting'))

        return request.redirect(request.link(self))

    layout = PASCommissionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New commission meeting'), '#'))

    return {
        'layout': layout,
        'title': _('New commission meeting'),
        'form': form,
        'form_width': 'large'
    }
