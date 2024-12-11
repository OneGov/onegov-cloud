from datetime import date
from decimal import Decimal
import transaction
from onegov.core.utils import Bunch
from onegov.pas.calculate_pay import calculate_rate
from onegov.pas.collections import AttendenceCollection
from onegov.pas.models import (
    Party,
    Parliamentarian,
    ParliamentarianRole,
    RateSet,
    Commission,
    SettlementRun,
    Attendence,
)
from onegov.pas.views.settlement_run import (
    _get_party_settlement_data,
    get_party_specific_totals,
)


def test_business_rules_export_data_for_party(session):
    """Test the business rules for party-specific exports."""

    with transaction.manager:
        # Create rate set with specific rates and COLA
        rate_set = RateSet(year=2024)
        rate_set.cost_of_living_adjustment = Decimal('5.0')  # 5% adjustment
        rate_set.plenary_none_president_halfday = 1000
        rate_set.plenary_none_member_halfday = 500
        rate_set.commission_normal_president_initial = 300
        rate_set.commission_normal_member_initial = 200
        rate_set.study_normal_president_halfhour = 100
        rate_set.study_normal_member_halfhour = 80
        session.add(rate_set)

        # Create two parties
        party_a = Party(name='Party A')
        party_b = Party(name='Party B')
        session.add_all([party_a, party_b])

        # Create a commission for testing commission attendences
        commission = Commission(name='Test Commission', type='normal')
        session.add(commission)

        # Create parliamentarians with roles
        jane = Parliamentarian(first_name='Jane', last_name='President')
        pres_role = ParliamentarianRole(
            parliamentarian=jane,
            role='president',
            party=party_a,
            start=date(2024, 1, 1),
        )

        mem = Parliamentarian(first_name='John', last_name='Member')
        mem_role = ParliamentarianRole(
            parliamentarian=mem,
            role='member',
            party=party_b,
            start=date(2024, 1, 1),
        )
        session.add_all([jane, mem, pres_role, mem_role])

        # Create settlement run
        run = SettlementRun(
            name='Q1 2024',
            start=date(2024, 1, 1),
            end=date(2024, 12, 31),
            active=True,
        )
        session.add(run)

        # Create various types of attendences
        attendences = [
            # Party A (President) attendences
            Attendence(
                parliamentarian=jane,
                date=date(2024, 1, 15),
                duration=240,  # 4 hours
                type='plenary',
            ),
            Attendence(
                parliamentarian=jane,
                date=date(2024, 1, 20),
                duration=180,  # 3 hours
                type='commission',
                commission=commission,
            ),
            Attendence(
                parliamentarian=jane,
                date=date(2024, 1, 25),
                duration=60,  # 1 hour
                type='study',
                commission=commission,
            ),

            # Party B (Member) attendences
            Attendence(
                parliamentarian=mem,
                date=date(2024, 2, 15),
                duration=240,  # 4 hours
                type='plenary',
            ),
            Attendence(
                parliamentarian=mem,
                date=date(2024, 2, 20),
                duration=180,  # 3 hours
                type='commission',
                commission=commission,
            ),
            Attendence(
                parliamentarian=mem,
                date=date(2024, 2, 25),
                duration=60,  # 1 hour
                type='study',
                commission=commission,
            ),
        ]
        session.add_all(attendences)
        session.flush()
        transaction.commit()

    # Test party-specific exports
    request = Bunch(session=session, translate=lambda x: str(x))

    # Test Party A exports
    party_a_data = _get_party_settlement_data(run, request, party_a)
    assert len(party_a_data) == 3  # Should have 3 attendences

    # Verify the data structure and values for Party A
    expected_party_a = [
        (
            date(2024, 1, 15),  # Plenary session
            'Jane President',
            'Plenary session',
            '0.5',
            Decimal('1000'),  # Base rate for president plenary
            Decimal('1050.00'),  # With 5% COLA
        ),
        (
            date(2024, 1, 20),  # Commission meeting
            'Jane President',
            'Commission meeting - Test Commission',
            '3.0',
            Decimal('300'),  # Base rate for president commission
            Decimal('315.00'),  # With 5% COLA
        ),
        (
            date(2024, 1, 25),  # Study session
            'Jane President',
            'File study - Test Commission',
            '1.0',
            Decimal('200'),  # Base rate for president study
            Decimal('210.00'),  # With 5% COLA
        ),
    ]
    assert party_a_data == sorted(expected_party_a, key=lambda x: x[0])

    # Test Party A totals
    party_a_totals = get_party_specific_totals(run, request, party_a)
    expected_totals = [
        (
            'Jane President',
            Decimal('1500'),  # Total meetings (1000 + 300 + 200)
            Decimal('0'),  # Expenses
            Decimal('1500'),  # Total before COLA
            Decimal('75'),  # COLA amount (5% of 1500)
            Decimal('1575'),  # Final amount with COLA
        ),
        (
            'Total Party A',
            Decimal('1500'),  # Same as above since only one person
            Decimal('0'),
            Decimal('1500'),
            Decimal('75'),
            Decimal('1575'),
        )
    ]
    assert party_a_totals == expected_totals

    # Test Party B exports (member rates should be lower)
    party_b_data = _get_party_settlement_data(run, request, party_b)
    assert len(party_b_data) == 3  # Should have 3 attendences

    expected_party_b = [
        (
            date(2024, 2, 15),  # Plenary session
            'John Member',
            'Plenary session',
            '0.5',
            Decimal('500'),  # Base rate for member plenary
            Decimal('525.00'),  # With 5% COLA
        ),
        (
            date(2024, 2, 20),  # Commission meeting
            'John Member',
            'Commission meeting - Test Commission',
            '3.0',
            Decimal('200'),  # Base rate for member commission
            Decimal('210.00'),  # With 5% COLA
        ),
        (
            date(2024, 2, 25),  # Study session
            'John Member',
            'File study - Test Commission',
            '1.0',
            Decimal('160'),  # Base rate for member study
            Decimal('168.00'),  # With 5% COLA
        ),
    ]
    assert party_b_data == sorted(expected_party_b, key=lambda x: x[0])

    # Test Party B totals
    party_b_totals = get_party_specific_totals(run, request, party_b)
    expected_totals = [
        (
            'John Member',
            Decimal('860'),  # Total meetings (500 + 200 + 160)
            Decimal('0'),  # Expenses
            Decimal('860'),  # Total before COLA
            Decimal('43'),  # COLA amount (5% of 860)
            Decimal('903'),  # Final amount with COLA
        ),
        (
            'Total Party B',
            Decimal('860'),  # Same as above since only one person
            Decimal('0'),
            Decimal('860'),
            Decimal('43'),
            Decimal('903'),
        )
    ]
    assert party_b_totals == expected_totals


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
        parliamentarian = Parliamentarian(
            first_name='Jane',
            last_name='President',
            gender='female'
        )
        party = Party(name='Test Party')
        role = ParliamentarianRole(
            parliamentarian=parliamentarian,
            role='president',
            party=party,
            start=date(2024, 1, 1),
        )
        session.add_all([parliamentarian, role, party])

        # Create commission
        commission = Commission(name='Test Commission', type='normal')
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
