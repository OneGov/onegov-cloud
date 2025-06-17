from __future__ import annotations

from onegov.core.elements import Link
from onegov.core.security import Private
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import CommissionCollection
from onegov.pas.forms import AttendenceAddCommissionForm
from onegov.pas.forms import CommissionMembershipAddForm
from onegov.pas.forms import CommissionForm
from onegov.pas.layouts import CommissionCollectionLayout
from onegov.pas.layouts import CommissionLayout
from onegov.pas.models import PASChange
from onegov.pas.models import PASCommission
from onegov.pas.models import PASCommissionMembership

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=CommissionCollection,
    template='commissions.pt',
    permission=Private
)
def view_commissions(
    self: CommissionCollection,
    request: TownRequest
) -> RenderData:

    layout = CommissionCollectionLayout(self, request)

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
        'commissions': self.query().all(),
        'title': layout.title,
    }


@PasApp.form(
    model=CommissionCollection,
    name='new',
    template='form.pt',
    permission=Private,
    form=CommissionForm
)
def add_commission(
    self: CommissionCollection,
    request: TownRequest,
    form: CommissionForm
) -> RenderData | Response:

    if form.submitted(request):
        commission = self.add(**form.get_useful_data())
        request.success(_('Added a new commission'))

        return request.redirect(request.link(commission))

    layout = CommissionCollectionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New'), '#'))
    layout.include_editor()

    return {
        'layout': layout,
        'title': _('New commission'),
        'form': form,
        'form_width': 'large'
    }


@PasApp.html(
    model=PASCommission,
    template='commission.pt',
    permission=Private
)
def view_commission(
    self: PASCommission,
    request: TownRequest
) -> RenderData:

    layout = CommissionLayout(self, request)

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
def edit_commission(
    self: PASCommission,
    request: TownRequest,
    form: CommissionForm
) -> RenderData | Response:

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = CommissionLayout(self, request)
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
    model=PASCommission,
    request_method='DELETE',
    permission=Private
)
def delete_commission(
    self: PASCommission,
    request: TownRequest
) -> None:

    request.assert_valid_csrf_token()

    collection = CommissionCollection(request.session)
    collection.delete(self)


@PasApp.form(
    model=PASCommission,
    name='new-membership',
    template='form.pt',
    permission=Private,
    form=CommissionMembershipAddForm
)
def add_commission_membership(
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

    layout = CommissionLayout(self, request)
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
def add_plenary_attendence(
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
            PASChange.add(request, 'add', attendence)
        request.success(_('Added commission meeting'))

        return request.redirect(request.link(self))

    layout = CommissionLayout(self, request)
    layout.breadcrumbs.append(Link(_('New commission meeting'), '#'))

    return {
        'layout': layout,
        'title': _('New commission meeting'),
        'form': form,
        'form_width': 'large'
    }
