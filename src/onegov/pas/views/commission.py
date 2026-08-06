from __future__ import annotations
from datetime import date
from itertools import groupby

from onegov.core.elements import Link
from onegov.core.security import Private, Public
from onegov.pas import PasApp
from onegov.pas.collections import PASCommissionCollection
from onegov.pas.i18n import _
from onegov.pas.layouts import PASCommissionCollectionLayout
from onegov.pas.layouts import PASCommissionLayout
from onegov.pas.models import PASCommission
from onegov.pas.models import PASCommissionMembership
from onegov.pas.utils import is_active_kantonsrat_member
from onegov.user import User

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.core.types import RenderData
    from onegov.pas.request import PasRequest
    from onegov.town6.request import TownRequest
    from webob import Response


@PasApp.html(
    model=PASCommissionCollection,
    template='commissions.pt',
    permission=Private
)
def pas_view_commissions(
    self: PASCommissionCollection, request: PasRequest
) -> RenderData | Response:
    layout = PASCommissionCollectionLayout(self, request)

    filters = {}
    filters['active'] = [
        Link(
            text=request.translate(title),
            active=self.active == value,
            url=request.link(self.for_filter(active=value)),
        )
        for title, value in ((_('Active'), True), (_('Inactive'), False))
    ]

    commissions = self.query().all()

    if not request.is_admin:
        p = request.current_parliamentarian
        if p:
            my_ids = {m.commission_id for m in p.commission_memberships}
            commissions = [c for c in commissions if c.id in my_ids]
        else:
            commissions = []

    return {
        'add_link': request.link(self, name='new'),
        'filters': filters,
        'layout': layout,
        'commissions': commissions,
        'title': layout.title,
    }


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

    presidents = []
    other_members = []

    for membership in self.memberships:
        if membership.role == 'president':
            presidents.append(membership)
        else:
            other_members.append(membership)

    president = None
    if presidents:
        active = [p for p in presidents if not p.end]
        president = active[0] if active else presidents[0]
        other_members.extend(
            p for p in presidents if p is not president
        )

    return {
        'layout': layout,
        'commission': self,
        'title': layout.title,
        'president': president,
        'other_members': other_members,
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
    if not request.is_admin:
        if (not hasattr(request.identity, 'role')
            or request.identity.role not in (
                'parliamentarian', 'commission_president')):
            return {}

    session = request.session
    today = date.today()
    memberships = [
        membership
        for membership in session.query(PASCommissionMembership).all()
        if membership.is_active_on(today)
    ]

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
            for m in user.parliamentarian.commission_memberships_on(  # type: ignore[attr-defined]
                on_date=today,
            )
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
            for m in user.parliamentarian.commission_memberships_on(  # type: ignore[attr-defined]
                on_date=today,
                role='president',
            )
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
            if is_active_kantonsrat_member(m.parliamentarian)
        ]
        for commission_id, group in groupby(sorted_memberships, key=key_func)
    }
