from datetime import date
from decimal import Decimal
import transaction
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
)


def test_parliamentarian_settlement_calculations(session):
    """Test the business logic for calculating parliamentarian settlements."""

    with transaction.manager:
        # Setup test data
        rate_set = RateSet(year=2024)
        rate_set.cost_of_living_adjustment = Decimal('5.0')  # 5% adjustment

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
            # Plenary sessions always count as half day
            assert base_rate == Decimal('1000')
            assert attendence.calculate_value() == Decimal('0.5')
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
