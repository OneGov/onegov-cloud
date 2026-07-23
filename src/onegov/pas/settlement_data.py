from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import or_

from onegov.pas.calculate_pay import Compensation
from onegov.pas.calculate_pay import calculate_attendance_compensation
from onegov.pas.calculate_pay import calculate_compensation
from onegov.pas.collections import AttendenceCollection
from onegov.pas.collections.presidential_allowance import (
    PresidentialAllowanceCollection,
)
from onegov.pas.custom import get_current_rate_set
from onegov.pas.models.attendence import TYPES
from onegov.pas.models.parliamentarian_role import PASParliamentarianRole
from onegov.pas.models.party import Party
from onegov.pas.models.presidential_allowance import (
    LOHNART_ALLOWANCE_TEXT,
)
from onegov.pas.utils import is_president_for_attendance


from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import date
    from uuid import UUID

    from sqlalchemy.orm import Session

    from onegov.pas.models import PASCommission
    from onegov.pas.models import PASParliamentarian
    from onegov.pas.models.attendence import AttendenceType
    from onegov.pas.models.settlement_run import SettlementRun
    from onegov.town6.request import TownRequest


@dataclass(frozen=True)
class SettlementAttendanceEntry:
    date: date
    parliamentarian: PASParliamentarian
    attendance_type: AttendenceType
    commission: PASCommission | None
    type_label: str
    type_description: str
    duration_minutes: Decimal
    value: Decimal
    compensation: Compensation


@dataclass(frozen=True)
class SettlementAllowanceEntry:
    date: date
    parliamentarian: PASParliamentarian
    type_description: str
    value: Decimal
    compensation: Compensation


type SettlementEntry = SettlementAttendanceEntry | SettlementAllowanceEntry


@dataclass(frozen=True)
class SettlementData:
    attendances: list[SettlementAttendanceEntry]
    allowances: list[SettlementAllowanceEntry]
    party_lookup: dict[UUID, Party | None]


def get_party_lookup(
    session: Session,
    parliamentarian_ids: set[UUID],
    start_date: date,
    end_date: date,
) -> dict[UUID, Party | None]:
    roles = (
        session.query(PASParliamentarianRole)
        .join(Party)
        .filter(
            PASParliamentarianRole.parliamentarian_id.in_(parliamentarian_ids),
            PASParliamentarianRole.party_id.isnot(None),
            or_(
                PASParliamentarianRole.end.is_(None),
                PASParliamentarianRole.end >= start_date,
            ),
            PASParliamentarianRole.start <= end_date,
        )
        .order_by(PASParliamentarianRole.start.desc())
        .all()
    )

    party_lookup = dict.fromkeys(parliamentarian_ids)
    for role in roles:
        if party_lookup[role.parliamentarian_id] is None:
            party_lookup[role.parliamentarian_id] = role.party
    return party_lookup


def get_settlement_data(
    settlement_run: SettlementRun,
    request: TownRequest,
) -> SettlementData:
    session = request.session
    rate_set = get_current_rate_set(session, settlement_run)
    if not rate_set:
        return SettlementData([], [], {})

    attendances = (
        AttendenceCollection(
            session,
            date_from=settlement_run.start,
            date_to=settlement_run.end,
        )
        .query()
        .all()
    )
    allowances = (
        PresidentialAllowanceCollection(
            session,
            settlement_run_id=settlement_run.id,
        )
        .query()
        .all()
    )
    parliamentarian_ids = {
        attendance.parliamentarian_id for attendance in attendances
    } | {allowance.parliamentarian_id for allowance in allowances}
    party_lookup = get_party_lookup(
        session,
        parliamentarian_ids,
        settlement_run.start,
        settlement_run.end,
    )

    attendance_entries = []
    for attendance in attendances:
        compensation = calculate_attendance_compensation(
            rate_set=rate_set,
            attendence_type=attendance.type,
            duration_minutes=attendance.duration,
            is_president=is_president_for_attendance(
                attendance.parliamentarian,
                attendance,
            ),
            commission_type=(
                attendance.commission.type if attendance.commission else None
            ),
        )
        type_label = request.translate(TYPES[attendance.type])
        type_description = type_label
        if attendance.commission:
            type_description = (
                f'{type_description} - {attendance.commission.name}'
            )
        attendance_entries.append(
            SettlementAttendanceEntry(
                date=attendance.date,
                parliamentarian=attendance.parliamentarian,
                attendance_type=attendance.type,
                commission=attendance.commission,
                type_label=type_label,
                type_description=type_description,
                duration_minutes=attendance.duration,
                value=attendance.calculate_value(),
                compensation=compensation,
            )
        )

    allowance_entries = [
        SettlementAllowanceEntry(
            date=settlement_run.end,
            parliamentarian=allowance.parliamentarian,
            type_description=LOHNART_ALLOWANCE_TEXT,
            value=Decimal('0'),
            compensation=calculate_compensation(
                allowance.amount,
                rate_set.cost_of_living_adjustment,
            ),
        )
        for allowance in allowances
    ]

    return SettlementData(
        attendances=attendance_entries,
        allowances=allowance_entries,
        party_lookup=party_lookup,
    )
