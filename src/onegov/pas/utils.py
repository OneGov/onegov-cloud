from __future__ import annotations

from onegov.pas import log
from onegov.pas.collections import AttendenceCollection
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.party import Party
from onegov.pas.models.parliamentarian import PASParliamentarian
from onegov.pas.models.parliamentarian_role import PASParliamentarianRole
from decimal import Decimal
from babel.numbers import format_decimal


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import SettlementRun
    from onegov.town6.request import TownRequest
    from datetime import date
    from sqlalchemy.orm import Session


def format_swiss_number(value: Decimal | int) -> str:
    if not isinstance(value, (Decimal, int)):
        raise TypeError(f'Expected Decimal or int, got {type(value).__name__}')

    if isinstance(value, int):
        value = Decimal(value)

    return format_decimal(value, format='#,##0.00', locale='de_CH')


def get_parliamentarians_with_settlements(
    session: Session,
    start_date: date,
    end_date: date
) -> list[PASParliamentarian]:
    """
    Get all parliamentarians who were active and had settlements during the
    specified period.
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

    roles_pretty_print = [
        f'{p.last_name} {p.first_name}: {p.roles}'
        for p in active_parliamentarians
    ]
    log.info(f'Active parliamentarians: {roles_pretty_print}')

    # Get all parliamentarians with attendances in one query
    parliamentarians_with_attendances = {
        pid[0] for pid in
        session.query(Attendence.parliamentarian_id).filter(
            Attendence.date >= start_date,
            Attendence.date <= end_date
        ).distinct()
    }
    log.info(f'Parli with attendances: {parliamentarians_with_attendances}')

    # Filter the active parliamentarians to only those with attendances
    return [
        p for p in active_parliamentarians
        if p.id in parliamentarians_with_attendances
    ]


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


# FIXME: Should these two functions be a CLI command instead? Maybe switch
#        to `click.echo` from `print` depending on the answer.
def debug_party_export(
    settlement_run: SettlementRun,
    request: TownRequest,
    party: Party
) -> None:
    """Debug function to trace party export data retrieval"""
    session = request.session

    # 1. Check basic party info
    print(f'Party ID: {party.id}, Name: {party.name}')  # noqa: T201

    # 2. Check date range
    print(f'Date range: {settlement_run.start} to {settlement_run.end}')  # noqa: T201

    # 3. Get all attendances without party filter first
    base_attendances = (
        AttendenceCollection(session)
        .query()
        .filter(
            Attendence.date >= settlement_run.start,
            Attendence.date <= settlement_run.end
        )
        .all()
    )
    print(f'Total attendances in date range: {len(base_attendances)}')  # noqa: T201

    # 4. Check parliamentarian roles
    for attendance in base_attendances:
        parl = attendance.parliamentarian
        print(f'\nParliamentarian: {parl.first_name} {parl.last_name}')  # noqa: T201
        print(f'Attendance date: {attendance.date}')  # noqa: T201

        roles = session.query(PASParliamentarianRole).filter(
            PASParliamentarianRole.parliamentarian_id == parl.id,
            PASParliamentarianRole.party_id == party.id,
            ).all()

        print('Roles:')  # noqa: T201
        for role in roles:
            print(f'- Start: {role.start}, End: {role.end}')  # noqa: T201

        # Check if this attendance should be included
        should_include = any(
            (role.start is None or role.start <= attendance.date) and
            (role.end is None or role.end >= attendance.date)
            for role in roles
        )
        print(f'Should include: {should_include}')  # noqa: T201

    # 5. Try the actual party filter
    party_attendances = (
        AttendenceCollection(session)
        .by_party(
            party_id=str(party.id),
            start_date=settlement_run.start,
            end_date=settlement_run.end
        )
        .query()
        .all()
    )
    print(f'\nFinal filtered attendances: {len(party_attendances)}')  # noqa: T201


def debug_party_export2(
    request: TownRequest,
    party: Party
) -> None:
    session = request.session
    print(f'Party ID: {party.id}')  # noqa: T201

    # Check roles directly
    all_roles = session.query(PASParliamentarianRole).filter(
        PASParliamentarianRole.party_id == party.id
    ).all()
    print(f'\nTotal roles for party: {len(all_roles)}')  # noqa: T201
    for role in all_roles:
        print(f'Role: {role.party_id} -> {role.parliamentarian_id}')  # noqa: T201

    # Check all parties
    all_parties = session.query(Party).all()
    print('\nAll parties:')  # noqa: T201
    for p in all_parties:
        print(f'ID: {p.id}, Name: {p.name}')  # noqa: T201
