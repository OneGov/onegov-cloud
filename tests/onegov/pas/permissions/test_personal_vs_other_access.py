from __future__ import annotations

import transaction

from datetime import date, timedelta
from onegov.pas.collections import (
    AttendenceCollection,
    PASCommissionCollection,
    PASParliamentarianCollection
)
from onegov.pas.models import PASCommissionMembership, SettlementRun
from onegov.user import UserCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import Attendence, PASCommission, PASParliamentarian
    from onegov.user import User
    from sqlalchemy.orm import Session
    from tests.shared.client import Client
    from uuid import UUID
    from ..conftest import TestPasApp

"""
  1. Own attendance: Parliamentarians can edit their own attendance
  2. Other's attendance: Parliamentarians CANNOT edit other parliamentarian's
     attendance
  3. Commission president powers: Can edit their commission members' attendance
  4. Commission boundaries: Cannot edit attendance from other commissions
  5. Personal details: Cannot view other parliamentarians' personal info

"""


def ensure_active_settlement_run(session: Session) -> SettlementRun:
    """Ensure there's an active settlement run for testing."""
    existing = session.query(SettlementRun).filter_by(closed=False).first()
    if existing:
        return existing

    today = date.today()
    settlement = SettlementRun(
        name=f'Test Settlement {today.year}',
        start=today - timedelta(days=30),
        end=today + timedelta(days=30),
        closed=False,
    )
    session.add(settlement)
    session.flush()
    return settlement


def create_parliamentarian_with_user(
    client: Client[TestPasApp],
    first_name: str,
    last_name: str,
    email: str,
    role: str = 'parliamentarian',
    password: str = 'test'
) -> tuple[PASParliamentarian, User]:
    """Helper to create a parliamentarian and set up their user account."""
    session = client.app.session()
    parliamentarians = PASParliamentarianCollection(client.app)

    parl = parliamentarians.add(
        first_name=first_name,
        last_name=last_name,
        email_primary=email
    )

    users = UserCollection(session)
    user = users.by_username(email)
    assert user is not None
    user.role = role
    user.password = password

    return parl, user


def create_attendance_for_parliamentarian(
    session: Session,
    parliamentarian_id: UUID,
    attendance_type: str = 'commission',
    duration: int = 120
) -> Attendence:
    """Helper to create attendance record for a parliamentarian."""
    attendences = AttendenceCollection(session)
    return attendences.add(
        parliamentarian_id=parliamentarian_id,
        type=attendance_type,
        date=date.today(),
        duration=duration
    )


def setup_commission_with_members(
    session: Session,
    commission_name: str,
    president_parl: PASParliamentarian,
    member_parl: PASParliamentarian
) -> PASCommission:
    """Helper to create commission and set up memberships."""
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name=commission_name)

    president_membership = PASCommissionMembership(
        parliamentarian_id=president_parl.id,
        commission_id=commission.id,
        role='president'
    )
    session.add(president_membership)

    member_membership = PASCommissionMembership(
        parliamentarian_id=member_parl.id,
        commission_id=commission.id,
        role='member'
    )
    session.add(member_membership)

    return commission


def setup_two_separate_commissions(
    session: Session,
    president_parl: PASParliamentarian,
    president_comm: str,
    member_parl: PASParliamentarian,
    member_comm: str
) -> tuple[PASCommission, PASCommission]:
    """Helper to create two separate commissions with different members."""
    commissions = PASCommissionCollection(session)
    commission1 = commissions.add(name=president_comm)
    commission2 = commissions.add(name=member_comm)

    president_membership = PASCommissionMembership(
        parliamentarian_id=president_parl.id,
        commission_id=commission1.id,
        role='president'
    )
    session.add(president_membership)

    member_membership = PASCommissionMembership(
        parliamentarian_id=member_parl.id,
        commission_id=commission2.id,
        role='member'
    )
    session.add(member_membership)

    return commission1, commission2


def test_parliamentarian_can_edit_own_attendance(
    client: Client[TestPasApp]
) -> None:
    """Parliamentarians should be able to edit their own attendance"""
    session = client.app.session()

    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )

    attendance_a = create_attendance_for_parliamentarian(session, parl_a.id)
    attendance_id_a = attendance_a.id
    transaction.commit()

    client.login('alice.parl@example.org', 'test')

    page = client.get(f'/attendence/{attendance_id_a}/edit')
    assert page.status_code == 200
    assert 'form' in page


def test_parliamentarian_cannot_edit_other_attendance(
    client: Client[TestPasApp]
) -> None:
    """Parliamentarian A should NOT be able to edit parliamentarian B's
    attendance"""
    session = client.app.session()

    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    attendance_b = create_attendance_for_parliamentarian(
        session, parl_b.id, duration=90
    )
    attendance_id_b = attendance_b.id
    transaction.commit()

    client.login('alice.parl@example.org', 'test')

    page = client.get(
        f'/attendence/{attendance_id_b}/edit', expect_errors=True
    )
    assert page.status_code in (403, 302)

    page = client.get(f'/attendence/{attendance_id_b}', expect_errors=True)
    assert page.status_code in (403, 302)


def test_commission_president_can_edit_member_attendance(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents should be able to edit attendance of their
    commission members"""
    session = client.app.session()

    president, _ = create_parliamentarian_with_user(
        client, 'President', 'Leader', 'president.leader@example.org',
        role='commission_president'
    )
    member, _ = create_parliamentarian_with_user(
        client, 'Member', 'Follower', 'member.follower@example.org'
    )

    setup_commission_with_members(session, 'Finance Commission',
                                president, member)

    member_attendance = create_attendance_for_parliamentarian(
        session, member.id, duration=180
    )
    attendance_id = member_attendance.id
    transaction.commit()

    client.login('president.leader@example.org', 'test')

    page = client.get(f'/attendence/{attendance_id}/edit')
    assert page.status_code == 200
    assert 'form' in page


def test_commission_president_cannot_edit_other_commission_attendance(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents should NOT be able to edit attendance of
    members from other commissions"""
    session = client.app.session()

    finance_president, _ = create_parliamentarian_with_user(
        client, 'Finance', 'President', 'finance.president@example.org',
        role='commission_president'
    )
    education_member, _ = create_parliamentarian_with_user(
        client, 'Education', 'Member', 'education.member@example.org'
    )

    setup_two_separate_commissions(
        session, finance_president, 'Finance Commission',
        education_member, 'Education Commission'
    )

    education_attendance = create_attendance_for_parliamentarian(
        session, education_member.id, duration=150
    )
    attendance_id = education_attendance.id
    transaction.commit()

    client.login('finance.president@example.org', 'test')

    page = client.get(f'/attendence/{attendance_id}/edit', expect_errors=True)
    assert page.status_code in (403, 302)


def test_parliamentarian_cannot_view_other_parliamentarian_details(
    client: Client[TestPasApp]
) -> None:
    """Parliamentarians should not be able to view other
    parliamentarians' personal details"""
    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    parl_a_id = parl_a.id
    parl_b_id = parl_b.id
    transaction.commit()

    client.login('alice.parl@example.org', 'test')

    # expect alice to be able to viwe their own attendence
    page = client.get(f'/parliamentarian/{parl_a_id}')
    # already this fails
    assert page.status_code == 200

    page = client.get(f'/parliamentarian/{parl_b_id}', expect_errors=True)
    assert page.status_code in (403, 302)


def test_attendance_collection_shows_only_own_records(
    client: Client[TestPasApp]
) -> None:

    session = client.app.session()
    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    create_attendance_for_parliamentarian(session, parl_a.id)
    create_attendance_for_parliamentarian(
        session, parl_b.id, attendance_type='plenary', duration=180
    )

    transaction.commit()

    client.login('alice.parl@example.org', 'test')
    page = client.get('/attendences')
    assert page.status_code == 200

    assert 'Alice' in page
    assert 'Bob' not in page
    assert ('Bob' not in page.text if hasattr(page, 'text')
            else 'Bob' not in str(page))


def test_admin_sees_all_attendance_records(
    client: Client[TestPasApp]
) -> None:
    """Admins should see all attendance records in /attendences"""
    session = client.app.session()

    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    users = UserCollection(session)
    admin_user = users.by_username('admin@example.org')
    assert admin_user is not None
    admin_user.password = 'test'

    create_attendance_for_parliamentarian(session, parl_a.id)
    create_attendance_for_parliamentarian(
        session, parl_b.id, attendance_type='plenary', duration=180
    )

    transaction.commit()

    client.login('admin@example.org', 'test')

    page = client.get('/attendences')
    assert page.status_code == 200

    assert 'Alice' in page
    assert 'Bob' in page


def test_parliamentarian_cannot_add_attendance_for_others(
    client: Client[TestPasApp]
) -> None:
    """Parliamentarians should not be able to add attendance for other
    parliamentarians"""
    session = client.app.session()

    ensure_active_settlement_run(session)

    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    parl_b_id = parl_b.id
    transaction.commit()

    client.login('alice.parl@example.org', 'test')

    form_page = client.get('/attendences/new')
    assert form_page.status_code == 200

    csrf_token = form_page.form['csrf_token'].value
    response = client.post(
        '/attendences/new',
        {
            'csrf_token': csrf_token,
            'parliamentarian_id': str(parl_b_id),
            'date': date.today().isoformat(),
            'duration': '2.0',
            'type': 'plenary',
        },
    )

    assert 'Sie können nur Ihre eigene Anwesenheit bearbeiten.' in response


def test_parliamentarian_can_only_see_self_in_dropdown(
    client: Client[TestPasApp]
) -> None:
    """Parliamentarians should only see themselves in the dropdown"""
    session = client.app.session()

    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    transaction.commit()

    client.login('alice.parl@example.org', 'test')

    page = client.get('/attendences/new')
    assert page.status_code == 200

    # Should only contain Alice's name, not Bob's
    assert 'Alice' in page
    assert 'Bob' not in page


def test_commission_president_can_add_for_commission_members(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents should be able to add attendance for their
    commission members"""
    session = client.app.session()

    ensure_active_settlement_run(session)

    president, _ = create_parliamentarian_with_user(
        client, 'President', 'Leader', 'president.leader@example.org',
        role='commission_president'
    )
    member, _ = create_parliamentarian_with_user(
        client, 'Member', 'Follower', 'member.follower@example.org'
    )

    setup_commission_with_members(session, 'Finance Commission',
                                president, member)

    member_id = member.id
    transaction.commit()

    client.login('president.leader@example.org', 'test')

    form_page = client.get('/attendences/new')
    assert form_page.status_code == 200

    assert 'Member' in form_page
    assert 'Follower' in form_page

    form_page.form['parliamentarian_id'] = str(member_id)
    form_page.form['date'] = date.today().isoformat()
    form_page.form['duration'] = '2.0'
    form_page.form['type'] = 'plenary'

    response = form_page.form.submit()
    assert 'Das Formular enthält Fehler' not in response

    error_msg = (
        'Sie können nur für sich selbst oder Ihre '
        'Kommissionsmitglieder Anwesenheiten bearbeiten.'
    )
    assert error_msg not in response

    transaction.commit()

    attendences = AttendenceCollection(session)
    query = attendences.query().filter_by(parliamentarian_id=member_id)
    created_attendance = query.first()

    assert created_attendance is not None
    assert created_attendance.parliamentarian_id == member_id
    assert created_attendance.type == 'plenary'


def test_commission_president_cannot_add_for_other_commission_members(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents should NOT be able to add attendance for members
    of other commissions"""
    session = client.app.session()

    ensure_active_settlement_run(session)

    finance_president, _ = create_parliamentarian_with_user(
        client, 'Finance', 'President', 'finance.president@example.org',
        role='commission_president'
    )
    education_member, _ = create_parliamentarian_with_user(
        client, 'Education', 'Member', 'education.member@example.org'
    )

    setup_two_separate_commissions(
        session, finance_president, 'Finance Commission',
        education_member, 'Education Commission'
    )

    education_member_id = education_member.id
    transaction.commit()

    client.login('finance.president@example.org', 'test')

    form_page = client.get('/attendences/new')
    assert form_page.status_code == 200

    csrf_token = form_page.form['csrf_token'].value
    response = client.post(
        '/attendences/new',
        {
            'csrf_token': csrf_token,
            'parliamentarian_id': str(education_member_id),
            'date': date.today().isoformat(),
            'duration': '2.0',
            'type': 'plenary',
        },
    )

    assert (
        'Sie können nur für sich selbst oder Ihre Kommissionsmitglieder '
        'Anwesenheiten bearbeiten.'
    ) in response
