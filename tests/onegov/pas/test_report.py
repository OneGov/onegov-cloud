from __future__ import annotations

from datetime import date
from onegov.pas.models import (
    Attendence,
    PASCommission,
    PASParliamentarian,
    RateSet,
    SettlementRun
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_generate_parliamentarian_export(session: Session) -> None:
    # Create parliamentarian
    parliamentarian = PASParliamentarian(
        first_name='John', last_name='Doe', gender='male'
    )
    session.add(parliamentarian)

    # Create settlement run for Q4 2023
    settlement_run = SettlementRun(
        name='Q4 2023',
        start=date(2023, 10, 1),
        end=date(2023, 12, 31),
        active=True,
    )
    session.add(settlement_run)

    # Create rate set for 2023
    rate_set = RateSet(  # type: ignore[misc]
        year=2023,
        cost_of_living_adjustment=2.0,  # 2% adjustment
        plenary_none_member_halfday=400,  # 100/hour after /4
        study_normal_member_halfhour=50,  # 100/hour after *2
        commission_normal_member_initial=100,  # direct hourly rate
    )
    session.add(rate_set)

    # Create test commission
    commission = PASCommission(name='Test PASCommission', type='normal')
    session.add(commission)
    session.flush()

    # Create some test attendances
    attendances = [
        # 2 hour plenary session
        Attendence(
            parliamentarian=parliamentarian,
            date=date(2023, 10, 15),
            duration=120,  # minutes
            type='plenary',
        ),
        # 1.5 hour commission meeting
        Attendence(
            parliamentarian=parliamentarian,
            date=date(2023, 11, 15),
            duration=90,  # minutes
            type='commission',
            commission=commission,
        ),
        # 1 hour study time
        Attendence(
            parliamentarian=parliamentarian,
            date=date(2023, 12, 15),
            duration=60,  # minutes
            type='study',
            commission=commission,
        ),
    ]
    for attendance in attendances:
        session.add(attendance)
    session.flush()

    # Generate export: single parliamentarian
    # FIXME: implement me
