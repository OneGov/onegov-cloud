from __future__ import annotations

from onegov.pas.models.attendence import Attendence
from onegov.pas.models.commission import PASCommission
from onegov.pas.models.commission_membership import PASCommissionMembership
from onegov.pas.models.party import Party
from onegov.pas.models.parliamentarian import PASParliamentarian
from onegov.pas.models.parliamentarian_role import PASParliamentarianRole
from onegov.pas.models.presidential_allowance import (
    PresidentialAllowance,
)
from decimal import Decimal, ROUND_HALF_UP
from babel.numbers import format_decimal
from datetime import date
from uuid import UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import SettlementRun
    from onegov.pas.models.attendence import Attendence
    from onegov.user import User
    from sqlalchemy.orm import Session


def _is_kantonsrat_role(
    role: PASParliamentarianRole,
) -> bool:
    """A Kantonsrat role has meta.org_type == 'Kantonsrat' (set
    by the KUB importer). Falls back to the legacy heuristic
    (all of party_id, parliamentary_group_id, and
    additional_information being NULL) for rows imported before
    org_type was persisted.
    """
    org_type = role.meta.get('org_type')
    if org_type is not None:
        return org_type == 'Kantonsrat'
    return (
        role.party_id is None
        and role.parliamentary_group_id is None
        and role.additional_information is None
    )


def is_active_kantonsrat_member(
    parliamentarian: PASParliamentarian,
    reference_date: date | None = None,
) -> bool:
    if reference_date is None:
        reference_date = date.today()
    return any(
        _is_kantonsrat_role(r) and (r.end is None or r.end >= reference_date)
        for r in parliamentarian.roles
    )


def format_swiss_number(value: Decimal | int) -> str:
    if not isinstance(value, (Decimal, int)):
        raise TypeError(f'Expected Decimal or int, got {type(value).__name__}')

    if isinstance(value, int):
        value = Decimal(value)

    return format_decimal(value, format='#,##0.00', locale='de_CH')


def round_to_five_rappen(value: Decimal | int) -> Decimal:
    """Round a decimal value to the nearest 5 Rappen (0.05 CHF)."""
    if isinstance(value, int):
        value = Decimal(value)

    return (value / Decimal('0.05')).quantize(
        Decimal('1'), rounding=ROUND_HALF_UP
    ) * Decimal('0.05')


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
