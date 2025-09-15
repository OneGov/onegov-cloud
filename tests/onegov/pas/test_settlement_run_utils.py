import transaction
from datetime import date

from onegov.pas.collections.commission import PASCommissionCollection
from onegov.pas.collections import PASParliamentarianCollection
from onegov.pas.collections.commission_membership import (
    PASCommissionMembershipCollection
)
from onegov.pas.collections import SettlementRunCollection
from onegov.pas.views.settlement_run import get_parliamentarian_closure_status
from onegov.pas.models import Attendence


def test_get_parliamentarian_closure_status(pas_app):
    """Test the get_parliamentarian_closure_status function."""
    session = pas_app.session()

    # Create test data: settlement run
    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='Test Settlement Run',
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        active=True
    )

    # Create parliamentarians
    parliamentarians = PASParliamentarianCollection(session)
    parl1 = parliamentarians.add(
        first_name='John',
        last_name='Doe',
        personnel_number='123'
    )
    parl2 = parliamentarians.add(
        first_name='Jane',
        last_name='Smith',
        personnel_number='456'
    )

    # Create commissions
    commissions = PASCommissionCollection(session)
    commission1 = commissions.add(name='Finance Commission')
    commission2 = commissions.add(name='Education Commission')

    # Create commission memberships
    memberships = PASCommissionMembershipCollection(session)
    # John is in Finance Commission
    memberships.add(
        commission_id=commission1.id,
        parliamentarian_id=parl1.id,
        role='member',
        start=date(2024, 1, 1)
    )
    # Jane is in both commissions
    memberships.add(
        commission_id=commission1.id,
        parliamentarian_id=parl2.id,
        role='member',
        start=date(2024, 1, 1)
    )
    memberships.add(
        commission_id=commission2.id,
        parliamentarian_id=parl2.id,
        role='president',
        start=date(2024, 1, 1)
    )

    # Create attendances
    # John has closed attendance for Finance Commission
    attendance1 = Attendence(
        date=date(2024, 6, 15),
        duration=120,
        type='commission',
        parliamentarian_id=parl1.id,
        commission_id=commission1.id,
        abschluss=True
    )
    session.add(attendance1)

    # Jane has open attendance for Finance Commission
    attendance2 = Attendence(
        date=date(2024, 6, 16),
        duration=90,
        type='commission',
        parliamentarian_id=parl2.id,
        commission_id=commission1.id,
        abschluss=False
    )
    session.add(attendance2)

    # Jane has closed attendance for Education Commission
    attendance3 = Attendence(
        date=date(2024, 6, 17),
        duration=150,
        type='commission',
        parliamentarian_id=parl2.id,
        commission_id=commission2.id,
        abschluss=True
    )
    session.add(attendance3)

    session.flush()
    transaction.commit()

    # Refresh the settlement run object to avoid detached instance issues
    session.refresh(settlement_run)

    # Test the function
    closure_status = get_parliamentarian_closure_status(session, settlement_run)

    # Verify results
    assert isinstance(closure_status, dict)

    # Check John Doe's status
    john_name = "John Doe"
    assert john_name in closure_status
    john_status = closure_status[john_name]
    assert "Finance Commission" in john_status
    assert john_status["Finance Commission"] is True  # Should be closed

    # Check Jane Smith's status
    jane_name = "Jane Smith"
    assert jane_name in closure_status
    jane_status = closure_status[jane_name]
    assert "Finance Commission" in jane_status
    assert jane_status["Finance Commission"] is False  # Should be open
    assert "Education Commission" in jane_status
    assert jane_status["Education Commission"] is True  # Should be closed


def test_get_parliamentarian_closure_status_no_attendances(pas_app):
    """Test closure status when parliamentarians have no attendances."""
    session = pas_app.session()

    # Create settlement run
    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='Empty Settlement Run',
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        active=True
    )

    # Create parliamentarian and commission
    parliamentarians = PASParliamentarianCollection(session)
    parl = parliamentarians.add(
        first_name='Bob',
        last_name='Wilson',
        personnel_number='789'
    )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Health Commission')

    # Create membership but no attendance
    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parl.id,
        role='member',
        start=date(2024, 1, 1)
    )

    session.flush()
    transaction.commit()

    # Refresh the settlement run object to avoid detached instance issues
    session.refresh(settlement_run)

    # Test function
    closure_status = get_parliamentarian_closure_status(session, settlement_run)

    # Verify Bob has commission but no closure (False)
    bob_name = "Bob Wilson"
    assert bob_name in closure_status
    bob_status = closure_status[bob_name]
    assert "Health Commission" in bob_status
    assert bob_status["Health Commission"] is False  # No closed attendance


def test_get_parliamentarian_closure_status_empty_data(pas_app):
    """Test closure status with empty data (no parliamentarians/commissions)."""
    session = pas_app.session()

    # Create settlement run but no data
    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='Empty Settlement Run',
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        active=True
    )

    session.flush()
    transaction.commit()

    # Refresh the settlement run object to avoid detached instance issues
    session.refresh(settlement_run)

    # Test function with empty data
    closure_status = get_parliamentarian_closure_status(session, settlement_run)

    # Should return empty dictionary
    assert isinstance(closure_status, dict)
    assert len(closure_status) == 0


def test_get_parliamentarian_closure_status_date_filtering(pas_app):
    """Test that closure status only considers attendances within settlement run dates."""
    session = pas_app.session()

    # Create settlement run for specific period
    settlement_runs = SettlementRunCollection(session)
    settlement_run = settlement_runs.add(
        name='Q1 Settlement Run',
        start=date(2024, 1, 1),
        end=date(2024, 3, 31),
        active=True
    )

    # Create parliamentarian and commission
    parliamentarians = PASParliamentarianCollection(session)
    parl = parliamentarians.add(
        first_name='Alice',
        last_name='Johnson',
        personnel_number='999'
    )

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Budget Commission')

    memberships = PASCommissionMembershipCollection(session)
    memberships.add(
        commission_id=commission.id,
        parliamentarian_id=parl.id,
        role='member',
        start=date(2024, 1, 1)
    )

    # Create attendance OUTSIDE settlement run period (should be ignored)
    attendance_outside = Attendence(
        date=date(2024, 5, 15),  # After settlement run end
        duration=120,
        type='commission',
        parliamentarian_id=parl.id,
        commission_id=commission.id,
        abschluss=True
    )
    session.add(attendance_outside)

    # Create attendance INSIDE settlement run period but not closed
    attendance_inside = Attendence(
        date=date(2024, 2, 15),  # Within settlement run period
        duration=90,
        type='commission',
        parliamentarian_id=parl.id,
        commission_id=commission.id,
        abschluss=False
    )
    session.add(attendance_inside)

    session.flush()
    transaction.commit()

    # Refresh the settlement run object to avoid detached instance issues
    session.refresh(settlement_run)

    # Test function
    closure_status = get_parliamentarian_closure_status(session, settlement_run)

    # Should only consider the attendance within the settlement period
    alice_name = "Alice Johnson"
    assert alice_name in closure_status
    alice_status = closure_status[alice_name]
    assert "Budget Commission" in alice_status
    # Should be False because the closed attendance is outside the period
    assert alice_status["Budget Commission"] is False
