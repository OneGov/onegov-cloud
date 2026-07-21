from __future__ import annotations

import niquests

from babel.numbers import format_decimal
from datetime import date
from decimal import Decimal
from lxml import html
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.commission import PASCommission
from onegov.pas.models.commission_membership import PASCommissionMembership
from onegov.pas.models.party import Party
from onegov.pas.models.parliamentarian import PASParliamentarian
from onegov.pas.models.parliamentarian_role import PASParliamentarianRole
from onegov.pas.models.presidential_allowance import (
    PresidentialAllowance,
)
from onegov.pas.collections import PASParliamentarianCollection
from sqlalchemy.orm import selectinload
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core import Framework
    from onegov.parliament.models.parliamentarian import Parliamentarian
    from onegov.parliament.models.parliamentarian_role import (
        ParliamentarianRole,
    )
    from onegov.pas.models import SettlementRun

    from onegov.user import User
    from sqlalchemy.orm import Session


def _is_kantonsrat_role(
    role: PASParliamentarianRole | ParliamentarianRole,
) -> bool:
    """A Kantonsrat role has meta.org_type == 'Kantonsrat' (set
    by the KUB importer).
    """
    org_type = role.meta.get('org_type')
    if org_type is not None:
        return org_type == 'Kantonsrat'
    return False


def is_active_kantonsrat_member(
    parliamentarian: PASParliamentarian | Parliamentarian,
    reference_date: date | None = None,
) -> bool:
    if reference_date is None:
        reference_date = date.today()
    return any(
        _is_kantonsrat_role(r) and (r.end is None or r.end >= reference_date)
        for r in parliamentarian.roles
    )


def get_active_kantonsrat_parliamentarians(
    app: Framework,
    reference_date: date | None = None,
) -> list[PASParliamentarian]:
    parliamentarians = (
        PASParliamentarianCollection(app)
        .query()
        .options(selectinload(PASParliamentarian.roles))
        .all()
    )
    return [
        p
        for p in parliamentarians
        if is_active_kantonsrat_member(p, reference_date)
    ]


CLEX_URL = 'https://zg-compwork.clex.ch/frontend/people'


def fetch_clex_kantonsrat_members(
    reference_date: date | None = None,
) -> set[tuple[str, str]]:
    """Fetch active Kantonsrat members from the CLEX frontend.

    Returns set of (last_name, first_name) tuples for members
    without an exit date or with an exit date >= reference_date.
    """
    if reference_date is None:
        reference_date = date.today()

    resp = niquests.get(CLEX_URL, timeout=30)
    resp.raise_for_status()
    assert resp.content is not None

    tree = html.fromstring(resp.content)
    rows = tree.xpath('//table//tr')

    members: set[tuple[str, str]] = set()
    for row in rows:
        cells = row.xpath('td')
        if len(cells) < 6:
            continue
        last_name = (cells[1].text_content() or '').strip()
        first_name = (cells[2].text_content() or '').strip()
        exit_text = (cells[6].text_content() or '').strip()
        if not last_name:
            continue

        if exit_text and exit_text != '—':
            try:
                parts = exit_text.split('.')
                exit_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
                if exit_date < reference_date:
                    continue
            except (ValueError, IndexError):
                pass

        members.add((last_name, first_name))
    return members


def format_swiss_number(value: Decimal | int) -> str:
    if not isinstance(value, (Decimal, int)):
        raise TypeError(f'Expected Decimal or int, got {type(value).__name__}')

    if isinstance(value, int):
        value = Decimal(value)

    return format_decimal(value, format='#,##0.00', locale='de_CH')


def is_kantonsrat_president(
    parliamentarian: PASParliamentarian,
    on_date: date,
) -> bool:
    """The Kantonsratspräsidium is a role on the parliamentarian and not a
    commission membership.

    """
    return any(
        role.role == 'president'
        and _is_kantonsrat_role(role)
        and (role.start is None or role.start <= on_date)
        and (role.end is None or role.end >= on_date)
        for role in parliamentarian.roles
    )


def is_president_for_attendance(
    parliamentarian: PASParliamentarian,
    attendance: Attendence,
    settlement_run: SettlementRun,
) -> bool:
    """Whether the president rate applies. A plenary session has no
    commission, there the Kantonsratspräsidium decides.

    """
    if attendance.type == 'plenary':
        return is_kantonsrat_president(parliamentarian, attendance.date)

    return is_commission_president(parliamentarian, attendance, settlement_run)


def is_commission_president(
    parliamentarian: PASParliamentarian,
    attendance_or_commission_id: Attendence | UUID,
    settlement_run: SettlementRun
) -> bool:
    """
    Check if a parliamentarian is president of the commission for the given
    attendance or commission_id during the settlement run period.
    """
    if isinstance(attendance_or_commission_id, UUID):
        commission_id = attendance_or_commission_id
        return any(
            cm.role == 'president'
            for cm in parliamentarian.commission_memberships
            if (
                cm.commission_id == commission_id and (
                    cm.end is None or cm.end >= settlement_run.start
                ) and (
                    cm.start is None or cm.start <= settlement_run.end
                )
            )
        )
    else:
        attendance = attendance_or_commission_id
        return any(
            cm.role == 'president'
            for cm in parliamentarian.commission_memberships
            if (
                attendance.commission and
                cm.commission_id == attendance.commission.id and (
                    cm.end is None or cm.end >= settlement_run.start
                ) and (
                    cm.start is None or cm.start <= settlement_run.end
                )
            )
        )


def get_parliamentarians_with_settlements(
    session: Session,
    start_date: date,
    end_date: date,
    settlement_run_id: UUID | None = None,
) -> list[PASParliamentarian]:
    """
    Get all parliamentarians who were active and had settlements
    (attendances or presidential allowances) during the specified
    period.
    """

    active_parliamentarians = session.query(PASParliamentarian).filter(
        PASParliamentarian.id.in_(
            session.query(PASParliamentarianRole.parliamentarian_id).filter(
                (PASParliamentarianRole.start.is_(None) | (
                            PASParliamentarianRole.start <= end_date)),
                (PASParliamentarianRole.end.is_(None) | (
                            PASParliamentarianRole.end >= start_date))
            )
        )
    ).order_by(
        PASParliamentarian.last_name,
        PASParliamentarian.first_name
    ).all()

    parliamentarians_with_attendances = {
        pid[0] for pid in
        session.query(Attendence.parliamentarian_id).filter(
            Attendence.date >= start_date,
            Attendence.date <= end_date
        ).distinct()
    }

    parliamentarians_with_allowances: set[UUID] = set()
    if settlement_run_id:
        parliamentarians_with_allowances = {
            pid[0]
            for pid in session.query(PresidentialAllowance.parliamentarian_id)
            .filter(
                PresidentialAllowance.settlement_run_id == settlement_run_id
            )
            .distinct()
        }

    eligible = (
        parliamentarians_with_attendances | parliamentarians_with_allowances
    )
    return [p for p in active_parliamentarians if p.id in eligible]


def get_parties_with_settlements(
    session: Session,
    start_date: date,
    end_date: date
) -> list[Party]:
    """
    Get all parties that had active members with attendances during the
    specified period.

    This function ensures accurate party filtering by checking that
    parliamentarians were active members of their party at the time of each
    attendance, properly handling cases where parliamentarians switch parties
    or have changing membership dates.

    """

    return (
        session.query(Party)
        .filter(
            Party.id.in_(
                session.query(PASParliamentarianRole.party_id)
                .join(PASParliamentarian)
                .join(
                    Attendence,
                    PASParliamentarian.id == Attendence.parliamentarian_id,
                )
                .filter(
                    Attendence.date >= start_date,
                    Attendence.date <= end_date,
                    PASParliamentarianRole.party_id.isnot(None),
                    (
                        PASParliamentarianRole.start.is_(None)
                        | (PASParliamentarianRole.start <= Attendence.date)
                    ),
                    (
                        PASParliamentarianRole.end.is_(None)
                        | (PASParliamentarianRole.end >= Attendence.date)
                    ),
                )
                .distinct()
            )
        )
        .order_by(Party.name)
        .all()
    )


def is_parliamentarian(user: User | None) -> bool:
    """Check if a user has parliamentarian role."""
    parls = {'parliamentarian', 'commission_president'}
    if not user:
        return False
    if user.role in parls:
        return True
    return False


def is_parliamentarian_role(role: str | None) -> bool:
    """Check if a role is a parliamentarian role."""
    parls = {'parliamentarian', 'commission_president'}
    return role in parls if role else False


def get_active_commission_memberships(
    user: User | None
) -> list[PASCommissionMembership]:
    """Get active commission memberships for a parliamentarian user."""
    if (not user or not hasattr(user, 'parliamentarian')
            or not user.parliamentarian):
        return []

    parliamentarian = user.parliamentarian
    return [
        m for m in parliamentarian.commission_memberships
        if not m.end or m.end >= date.today()
    ]


def get_commissions_with_memberships(
    session: Session,
    start_date: date,
    end_date: date
) -> list[PASCommission]:
    """
    Get all commissions that had active memberships during the
    specified period.

    This function ensures accurate commission filtering by checking that
    commissions had active members during the period, properly handling
    cases where memberships have changing dates.
    """

    return (
        session.query(PASCommission)
        .filter(
            PASCommission.id.in_(
                session.query(PASCommissionMembership.commission_id)
                .filter(
                    (
                        PASCommissionMembership.start.is_(None)
                        | (PASCommissionMembership.start <= end_date)
                    ),
                    (
                        PASCommissionMembership.end.is_(None)
                        | (PASCommissionMembership.end >= start_date)
                    ),
                )
                .distinct()
            )
        )
        .order_by(PASCommission.name)
        .all()
    )
