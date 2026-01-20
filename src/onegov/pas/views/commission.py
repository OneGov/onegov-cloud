from __future__ import annotations
from itertools import groupby

from onegov.core.elements import Link
from onegov.core.security import Private, Public
from onegov.org.forms.commission_membership import CommissionMembershipAddForm
from onegov.town6.views.commission import (
    view_commissions,
    add_commission,
    delete_commission
)
from onegov.pas import _
from onegov.pas import PasApp
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.forms import AttendenceAddCommissionForm
from onegov.pas.forms import CommissionForm
from onegov.pas.layouts import PASCommissionCollectionLayout
from onegov.pas.layouts import PASCommissionLayout
from onegov.pas.custom import check_attendance_in_closed_settlement_run
from onegov.pas.models import Change
from onegov.pas.models import PASCommission
from onegov.pas.models import PASCommissionMembership
from onegov.user import User

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
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

    president = None
    other_members = []

    for membership in self.memberships:
        if membership.role == 'president':
            president = membership
        else:
            other_members.append(membership)

    return {
        'layout': layout,
        'commission': self,
        'title': layout.title,
        'president': president,
        'other_members': other_members,
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

    if form.submitted(request):
        form.populate_obj(self)
        request.success(_('Your changes were saved'))
        return request.redirect(request.link(self))

    form.process(obj=self)

    layout = PASCommissionLayout(self, request)
    layout.breadcrumbs.append(Link(_('Edit'), '#'))
    layout.include_editor()
    layout.edit_mode = True

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
        # Check if attendance date is in a closed settlement run
        if form.date.data:
            if check_attendance_in_closed_settlement_run(
                request.session, form.date.data
            ):
                request.alert(
                    _('Cannot create attendance in closed settlement run.')
                )
                return {
                    'layout': PASCommissionLayout(self, request),
                    'title': _('New commission meeting'),
                    'form': form,
                    'form_width': 'large'
                }

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


@PasApp.json(
    model=PASCommissionCollection,
    name='commissions-parliamentarians-json',
    permission=Public,
)
def commissions_parliamentarians_json(
    self: PASCommissionCollection, request: TownRequest
) -> JSON_ro:
    """Returns all commissions with their parliamentarians."""
    # TODO: Should we consider all that have been active in
    # current settlement run to be more precise?
    # It might happen that some have been active just recently
    # but not anymore, these will not be selectable currently.
    if not request.is_admin:
        if (not hasattr(request.identity, 'role')
            or request.identity.role not in (
                'parliamentarian', 'commission_president')):
            return {}

    session = request.session
    memberships = session.query(PASCommissionMembership).all()

    # If user is parliamentarian, filter to only their commissions
    if (hasattr(request.identity, 'role')
        and request.identity.role == 'parliamentarian'):
        user = session.query(User).filter_by(
            username=request.identity.userid
        ).first()

        if not user or not user.parliamentarian:  # type: ignore[attr-defined]
            return {}

        # Get commission IDs where this parliamentarian is a member
        parliamentarian_commission_ids = {
            str(m.commission_id)
            for m in user.parliamentarian.commission_memberships  # type: ignore[attr-defined]
        }

        # Filter memberships to only those commissions
        valid_memberships = (
            m for m in memberships
            if m.parliamentarian
            and str(m.commission_id) in parliamentarian_commission_ids
        )
    # If user is commission_president, filter to only their commissions
    elif (hasattr(request.identity, 'role')
        and request.identity.role == 'commission_president'):
        user = session.query(User).filter_by(
            username=request.identity.userid
        ).first()

        if not user or not user.parliamentarian:  # type: ignore[attr-defined]
            return {}

        # Get commission IDs where this user is president
        president_commission_ids = {
            str(m.commission_id)
            for m in user.parliamentarian.commission_memberships  # type: ignore[attr-defined]
            if m.role == 'president'
        }

        # Filter memberships to only those commissions
        valid_memberships = (
            m for m in memberships
            if m.parliamentarian
            and str(m.commission_id) in president_commission_ids
        )
    else:
        # Admin gets all commissions
        valid_memberships = (m for m in memberships if m.parliamentarian)

    def key_func(m: PASCommissionMembership) -> str:
        return str(m.commission_id)

    # Note: Iterable passed into groupby needs to be sorted
    sorted_memberships = sorted(valid_memberships, key=key_func)

    return {
        commission_id: [
            {
                'id': str(m.parliamentarian.id),
                'title': m.parliamentarian.title
            }
            for m in group
        ]
        for commission_id, group in groupby(sorted_memberships, key=key_func)
    }
