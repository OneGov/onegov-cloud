import transaction
from datetime import date

from onegov.pas.collections.commission import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections.commission_membership import (
    PASCommissionMembershipCollection
)
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.views.settlement_run import get_commission_closure_status
from onegov.pas.models import Attendence


def test_get_commission_closure_status(pas_app):
    """Test the get_commission_closure_status function comprehensively."""
    session = pas_app.session()

    # Create settlement run for specific period
    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='Test Settlement Run',
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        active=True
    )

    # Create parliamentarians
    parliamentarians = PASParliamentarianCollection(pas_app)
    john = parliamentarians.add(
        first_name='John',
        last_name='Doe',
        personnel_number='123'
    )
    jane = parliamentarians.add(
        first_name='Jane',
        last_name='Smith',
        personnel_number='456'
    )
    bob = parliamentarians.add(
        first_name='Bob',
        last_name='Wilson',
        personnel_number='789'
    )
    alice = parliamentarians.add(
        first_name='Alice',
        last_name='Johnson',
        personnel_number='999'
    )

    # Create commissions
    commissions = PASCommissionCollection(session)
    finance_commission = commissions.add(name='Finance Commission')
    education_commission = commissions.add(name='Education Commission')
    health_commission = commissions.add(name='Health Commission')
    budget_commission = commissions.add(name='Budget Commission')

    # Create commission memberships
    memberships = PASCommissionMembershipCollection(session)

    # John in Finance Commission
    memberships.add(
        commission_id=finance_commission.id,
        parliamentarian_id=john.id,
        role='member',
        start=date(2024, 1, 1)
    )

    # Jane in both Finance and Education
    memberships.add(
        commission_id=finance_commission.id,
        parliamentarian_id=jane.id,
        role='member',
        start=date(2024, 1, 1)
    )
    memberships.add(
        commission_id=education_commission.id,
        parliamentarian_id=jane.id,
        role='president',
        start=date(2024, 1, 1)
    )

    # Bob in Health Commission (no attendance)
    memberships.add(
        commission_id=health_commission.id,
        parliamentarian_id=bob.id,
        role='member',
        start=date(2024, 1, 1)
    )

    # Alice in Budget Commission (for date filtering test)
    memberships.add(
        commission_id=budget_commission.id,
        parliamentarian_id=alice.id,
        role='member',
        start=date(2024, 1, 1)
    )

    # Create attendances
    # John has closed attendance for Finance Commission
    attendance1 = Attendence(
        date=date(2024, 6, 15),
        duration=120,
        type='commission',
        parliamentarian_id=john.id,
        commission_id=finance_commission.id,
        abschluss=True
    )
    session.add(attendance1)

    # Jane has open attendance for Finance Commission
    attendance2 = Attendence(
        date=date(2024, 6, 16),
        duration=90,
        type='commission',
        parliamentarian_id=jane.id,
        commission_id=finance_commission.id,
        abschluss=False
    )
    session.add(attendance2)

    # Jane has closed attendance for Education Commission
    attendance3 = Attendence(
        date=date(2024, 6, 17),
        duration=150,
        type='commission',
        parliamentarian_id=jane.id,
        commission_id=education_commission.id,
        abschluss=True
    )
    session.add(attendance3)

    # Alice has attendance OUTSIDE settlement run period (for next test)
    # This will be tested in a separate settlement run
    attendance_outside = Attendence(
        date=date(2026, 5, 15),  # After any settlement run end
        duration=120,
        type='commission',
        parliamentarian_id=alice.id,
        commission_id=budget_commission.id,
        abschluss=True
    )
    session.add(attendance_outside)

    # Alice has attendance INSIDE settlement run period but not closed
    attendance_inside = Attendence(
        date=date(2024, 2, 15),  # Within settlement run period
        duration=90,
        type='commission',
        parliamentarian_id=alice.id,
        commission_id=budget_commission.id,
        abschluss=False
    )
    session.add(attendance_inside)

    session.flush()
    transaction.commit()

    # Re-attach the settlement run object to avoid detached instance issues
    settlement_run = session.merge(settlement_run)

    # Test 1: Basic functionality with mixed statuses
    commission_status = get_commission_closure_status(session, settlement_run)
    assert isinstance(commission_status, list)

    # Should have 4 commissions
    assert len(commission_status) == 4

    # Find specific commissions in the results
    finance_status = next(
        (c for c in commission_status
         if c['commission_name'] == 'Finance Commission'), None
    )
    education_status = next(
        (c for c in commission_status
         if c['commission_name'] == 'Education Commission'), None
    )
    health_status = next(
        (c for c in commission_status
         if c['commission_name'] == 'Health Commission'), None
    )
    budget_status = next(
        (c for c in commission_status
         if c['commission_name'] == 'Budget Commission'), None
    )

    assert finance_status is not None
    assert education_status is not None
    assert health_status is not None
    assert budget_status is not None

    # Check Finance Commission (John completed, Jane not completed)
    assert finance_status['total_members'] == 2
    assert finance_status['completed_members'] == 1
    assert finance_status['completion_ratio'] == '1/2'
    assert finance_status['is_complete'] is False
    assert len(finance_status['complete_members']) == 1
    assert finance_status['complete_members'][0]['name'] == 'John Doe'
    assert len(finance_status['incomplete_members']) == 1
    assert finance_status['incomplete_members'][0]['name'] == 'Jane Smith'
    assert finance_status['incomplete_members'][0]['has_attendance'] is True

    # Check Education Commission (only Jane, completed)
    assert education_status['total_members'] == 1
    assert education_status['completed_members'] == 1
    assert education_status['completion_ratio'] == '1/1'
    assert education_status['is_complete'] is True
    assert len(education_status['complete_members']) == 1
    assert education_status['complete_members'][0]['name'] == 'Jane Smith'
    assert len(education_status['incomplete_members']) == 0

    # Check Health Commission (only Bob, no attendance)
    assert health_status['total_members'] == 1
    assert health_status['completed_members'] == 0
    assert health_status['completion_ratio'] == '0/1'
    assert health_status['is_complete'] is False
    assert len(health_status['complete_members']) == 0
    assert len(health_status['incomplete_members']) == 1
    assert health_status['incomplete_members'][0]['name'] == 'Bob Wilson'
    assert health_status['incomplete_members'][0]['has_attendance'] is False

    # Check Budget Commission (Alice has attendance but not closed)
    assert budget_status['total_members'] == 1
    assert budget_status['completed_members'] == 0
    assert budget_status['completion_ratio'] == '0/1'
    assert budget_status['is_complete'] is False
    assert len(budget_status['complete_members']) == 0
    assert len(budget_status['incomplete_members']) == 1
    assert budget_status['incomplete_members'][0]['name'] == 'Alice Johnson'
    assert budget_status['incomplete_members'][0]['has_attendance'] is True

    # Test 2: Settlement period with no attendances
    # (commissions exist but no attendance activity)
    no_attendance_settlement = settlement_runs.add(
        name='No Attendance Settlement Run',
        start=date(2025, 1, 1),
        end=date(2025, 12, 31),
        active=True
    )
    session.flush()
    transaction.commit()
    no_attendance_settlement = session.merge(no_attendance_settlement)

    no_attendance_status = get_commission_closure_status(
        session, no_attendance_settlement
    )
    assert isinstance(no_attendance_status, list)
    # Should have 4 commissions but all with 0 completion since no attendances
    assert len(no_attendance_status) == 4

    for commission in no_attendance_status:
        assert commission['completed_members'] == 0
        assert commission['completion_ratio'].startswith('0/')
        assert commission['is_complete'] is False
        assert len(commission['complete_members']) == 0
        # All members should be in incomplete list with no attendance
        for member in commission['incomplete_members']:
            assert member['has_attendance'] is False
