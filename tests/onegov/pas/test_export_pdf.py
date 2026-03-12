from __future__ import annotations

import transaction

from datetime import date
from decimal import Decimal
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import AttendenceCollection
from onegov.pas.models import (
    Party,
    PASParliamentarian,
    PASParliamentarianRole,
    RateSet,
    PASCommission,
    SettlementRun,
    Attendence,
    PASCommissionMembership,
)
from onegov.pas.views.settlement_run import _get_commission_settlement_data
from onegov.town6.request import TownRequest
from unittest.mock import Mock


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_parliamentarian_settlement_calculations(session: Session) -> None:
    """Test the business logic for calculating parliamentarian settlements."""

    with transaction.manager:
        # Setup test data
        rate_set = RateSet(year=2024)
        rate_set.cost_of_living_adjustment = 5.0  # 5% adjustment

        # Set rates
        rate_set.plenary_none_president_halfday = 1000
        rate_set.plenary_none_member_halfday = 500
        rate_set.commission_normal_president_initial = 300
        rate_set.commission_normal_member_initial = 200
        rate_set.commission_normal_president_additional = 100
        rate_set.commission_normal_member_additional = 80
        rate_set.study_normal_president_halfhour = 100
        rate_set.study_normal_member_halfhour = 80
        session.add(rate_set)

        # Create parliamentarian with president role
        parliamentarian = PASParliamentarian(
            first_name='Jane',
            last_name='President',
            gender='female'
        )
        party = Party(name='Test Party')
        role = PASParliamentarianRole(
            parliamentarian=parliamentarian,
            role='president',
            party=party,
            start=date(2024, 1, 1),
        )
        session.add_all([parliamentarian, role, party])

        # Create commission
        commission = PASCommission(name='Test PASCommission', type='normal')
        session.add(commission)

        # Create various attendances to test different scenarios
        attendences = [
            # Plenary session (always counts as half day)
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 15),
                duration=240,  # 4 hours - should still count as half day
                type='plenary'
            ),

            # Commission meetings
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 20),
                duration=120,  # 2 hours - initial rate only
                type='commission',
                commission=commission
            ),
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 1, 21),
                duration=180,  # 3 hours - initial + additional rate
                type='commission',
                commission=commission
            ),

            # Study sessions
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 2, 1),
                duration=60,  # 1 hour
                type='study',
                commission=commission
            ),
            Attendence(
                parliamentarian=parliamentarian,
                date=date(2024, 2, 2),
                duration=90,  # 1.5 hours
                type='study',
                commission=commission
            )
        ]
        session.add_all(attendences)

        # Create settlement run
        run = SettlementRun(
            name='Q1 2024',
            start=date(2024, 1, 1),
            end=date(2024, 3, 31),
            active=True,
        )
        session.add(run)
        session.flush()
        transaction.commit()

    # Test individual rate calculations
    for attendence in AttendenceCollection(session).query():
        base_rate = calculate_rate(
            rate_set=rate_set,
            attendence_type=attendence.type,
            duration_minutes=int(attendence.duration),
            is_president=True,
            commission_type=(
                attendence.commission.type if attendence.commission else None
            ),
        )

        if attendence.type == 'plenary':
            # Plenary sessions: CHF always half day, but value shows actual hrs
            assert base_rate == Decimal('1000')
            # Actual duration was 240 minutes (4 hours)
            assert attendence.calculate_value() == Decimal('4.0')
        elif attendence.type == 'commission':
            if attendence.duration == 120:  # 2 hour meeting
                assert base_rate == Decimal('300')  # Initial rate only
                assert attendence.calculate_value() == Decimal('2.0')
            elif attendence.duration == 180:  # 3 hour meeting
                # Initial rate (300) + 2 additional half hours (2 * 100)
                assert base_rate == Decimal('500')
                assert attendence.calculate_value() == Decimal('3.0')
        elif attendence.type == 'study':
            if attendence.duration == 60:  # 1 hour
                # 2 half-hour periods at 100 each
                assert base_rate == Decimal('200')
                assert attendence.calculate_value() == Decimal('1.0')
            elif attendence.duration == 90:  # 1.5 hours
                # 3 half-hour periods at 100 each
                assert base_rate == Decimal('300')
                assert attendence.calculate_value() == Decimal('1.5')


    # Test total calculations for the settlement period
    session.expire_all()  # Ensure all instances are refreshed from the db
    attendences = AttendenceCollection(
        session,
        date_from=run.start,
        date_to=run.end,
        parliamentarian_id=str(parliamentarian.id)
    ).query().all()

    total_base = sum(
        calculate_rate(
            rate_set=rate_set,
            attendence_type=a.type,
            duration_minutes=int(a.duration),
            is_president=True,
            commission_type=a.commission.type if a.commission else None
        ) for a in attendences
    )

    # Expected calculations:
    # 1. Plenary (half day): 1000
    # 2. Commission (2h): 300
    # 3. Commission (3h): 500
    # 4. Study (1h): 200
    # 5. Study (1.5h): 300
    expected_base = Decimal('2300')
    assert total_base == expected_base

    # Test COLA calculations
    cola_amount = total_base * Decimal('0.05')  # 5% adjustment
    assert cola_amount == Decimal('115')

    final_total = total_base + cola_amount
    assert final_total == Decimal('2415')

def test_commission_export_one_member_one_president(session: Session) -> None:
    """Test commission export with one member and one president."""


    with transaction.manager:
        # Create rate set with actual current values
        rate_set = RateSet(year=2025)
        rate_set.cost_of_living_adjustment = 21.935

        rate_set.plenary_none_member_halfday = 184
        rate_set.shortest_all_member_halfhour = 26
        rate_set.study_normal_member_halfhour = 26
        rate_set.plenary_none_president_halfday = 307
        rate_set.study_official_member_halfhour = 84
        rate_set.shortest_all_president_halfhour = 26
        rate_set.study_intercantonal_member_hour = 86
        rate_set.study_normal_president_halfhour = 43
        rate_set.commission_normal_member_initial = 104
        rate_set.study_official_president_halfhour = 84
        rate_set.study_intercantonal_president_hour = 86
        rate_set.commission_normal_member_additional = 26
        rate_set.commission_normal_president_initial = 104
        rate_set.commission_official_president_fullday = 369
        rate_set.commission_official_president_halfday = 184
        rate_set.commission_normal_president_additional = 26
        rate_set.commission_intercantonal_member_halfday = 147
        rate_set.commission_intercantonal_president_halfday = 246
        rate_set.commission_official_vice_president_fullday = 369
        rate_set.commission_official_vice_president_halfday = 184
        session.add(rate_set)

        # Create commission
        commission = PASCommission(name='Test Commission', type='normal')
        session.add(commission)

        # Create parliamentarians
        president = PASParliamentarian(
            first_name='Anna',
            last_name='President',
            gender='female'
        )
        member = PASParliamentarian(
            first_name='Max',
            last_name='Member',
            gender='male'
        )
        session.add_all([president, member])

        # Create party and roles
        party = Party(name='Test Party')
        session.add(party)

        president_role = PASParliamentarianRole(
            parliamentarian=president,
            role='member',
            party=party,
            start=date(2025, 1, 1),
        )
        member_role = PASParliamentarianRole(
            parliamentarian=member,
            role='member',
            party=party,
            start=date(2025, 1, 1),
        )
        session.add_all([president_role, member_role])

        # Create commission memberships
        president_membership = PASCommissionMembership(
            commission=commission,
            parliamentarian=president,
            role='president',
            start=date(2025, 1, 1)
        )
        member_membership = PASCommissionMembership(
            commission=commission,
            parliamentarian=member,
            role='member',
            start=date(2025, 1, 1)
        )
        session.add_all([president_membership, member_membership])

        # Create attendances
        attendances = [
            Attendence(
                parliamentarian=president,
                date=date(2025, 2, 15),
                duration=60,  # 1 hour
                type='study',
                commission=commission
            ),
            Attendence(
                parliamentarian=member,
                date=date(2025, 2, 15),
                duration=60,  # 1 hour
                type='study',
                commission=commission
            ),
        ]
        session.add_all(attendances)

        # Create settlement run
        settlement_run = SettlementRun(
            name='Q1 2025 Test',
            start=date(2025, 1, 1),
            end=date(2025, 3, 31),
            active=True,
        )
        session.add(settlement_run)
        session.flush()
        transaction.commit()

    mock_request = Mock(spec=TownRequest)
    mock_request.session = session
    mock_request.translate = lambda x: x

    # Test the commission export function
    settlement_data = _get_commission_settlement_data(
        settlement_run, mock_request, commission
    )
    assert len(settlement_data) == 2
    settlement_data.sort(key=lambda x: x[1].last_name)

    # Verify member data (non-president)
    member_row = settlement_data[0]  # Member comes first alphabetically
    assert member_row[2] == 'File study'  # attendance type
    assert member_row[3] == Decimal('1.0')  # calculated value (1 hour)
    assert member_row[4] == Decimal('52')  # base rate (26 * 2 half-hours)
    expected_cola_member = Decimal('52') * Decimal('1.21935')  # 21.935% COLA
    assert member_row[5] == expected_cola_member

    # Verify president data
    president_row = settlement_data[1]  # President comes second alphabetically
    assert president_row[2] == 'File study'  # attendance type
    assert president_row[3] == Decimal('1.0')  # calculated value (1 hour)
    assert president_row[4] == Decimal('86')  # base rate (43 * 2 half-hours)
    expected_cola_president = Decimal('86') * Decimal('1.21935')  # COLA
    assert president_row[5] == expected_cola_president
