from onegov.pas.collections import (
    AttendenceCollection,
    PASCommissionCollection,
    PASParliamentarianCollection
)
from onegov.pas.models import PASCommissionMembership
from onegov.user import UserCollection
import transaction
from datetime import date

"""
  1. Own attendance: Parliamentarians can edit their own attendance
  2. Other's attendance: Parliamentarians CANNOT edit other parliamentarian's
     attendance
  3. Commission president powers: Can edit their commission members' attendance
  4. Commission boundaries: Cannot edit attendance from other commissions
  5. Personal details: Cannot view other parliamentarians' personal info

"""


def create_parliamentarian_with_user(client, first_name: str, last_name: str,
                                    email: str, role: str = 'parliamentarian',
                                    password: str = 'test'):
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
    user.role = role
    user.password = password

    return parl, user


def create_attendance_for_parliamentarian(session, parliamentarian_id: str,
                                        attendance_type: str = 'commission',
                                        duration: int = 120):
    """Helper to create attendance record for a parliamentarian."""
    attendences = AttendenceCollection(session)
    return attendences.add(
        parliamentarian_id=parliamentarian_id,
        type=attendance_type,
        date=date.today(),
        duration=duration
    )


def setup_commission_with_members(session, commission_name: str,
                                president_parl, member_parl):
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


def setup_two_separate_commissions(session, president_parl, president_comm,
                                 member_parl, member_comm):
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


def test_parliamentarian_can_edit_own_attendance(client):
    '''Parliamentarians should be able to edit their own attendance'''
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


def test_parliamentarian_cannot_edit_other_attendance(client):
    '''Parliamentarian A should NOT be able to edit parliamentarian B\'s
    attendance'''
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


def test_commission_president_can_edit_member_attendance(client):
    '''Commission presidents should be able to edit attendance of their
    commission members'''
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


def test_commission_president_cannot_edit_other_commission_attendance(client):
    '''Commission presidents should NOT be able to edit attendance of
    members from other commissions'''
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


def test_parliamentarian_cannot_view_other_parliamentarian_details(client):
    '''Parliamentarians should not be able to view other
    parliamentarians\' personal details'''
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


def test_attendance_collection_shows_only_own_records(client):
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


def test_admin_sees_all_attendance_records(client):
    '''Admins should see all attendance records in /attendences'''
    session = client.app.session()

    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    users = UserCollection(session)
    admin_user = users.by_username('admin@example.org')
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


def test_parliamentarian_cannot_add_attendance_for_others(client):
    '''Parliamentarians should not be able to add attendance for other
    parliamentarians'''
    session = client.app.session()

    parl_a, _ = create_parliamentarian_with_user(
        client, 'Alice', 'Parliamentarian', 'alice.parl@example.org'
    )
    parl_b, _ = create_parliamentarian_with_user(
        client, 'Bob', 'Parliamentarian', 'bob.parl@example.org'
    )

    parl_b_id = parl_b.id
    transaction.commit()

    client.login('alice.parl@example.org', 'test')

    # Get the form page first to extract CSRF token
    form_page = client.get('/attendences/new')
    assert form_page.status_code == 200

    # Try to submit form with Bob's ID (form manipulation)
    page = client.post('/attendences/new', {
        'parliamentarian_id': str(parl_b_id),
        'date': '2024-01-15',
        'duration': '2.0',
        'type': 'plenary',
    })

    # Should get validation error
    assert 'You can only add attendance for yourself' in page


def test_parliamentarian_can_only_see_self_in_dropdown(client):
    '''Parliamentarians should only see themselves in the dropdown'''
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


def test_commission_president_can_add_for_commission_members(client):
    '''Commission presidents should be able to add attendance for their
    commission members'''
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

    member_id = member.id
    transaction.commit()

    client.login('president.leader@example.org', 'test')

    # Should be able to add attendance for commission member
    page = client.post('/attendences/new', {
        'parliamentarian_id': str(member_id),
        'date': '2024-01-15',
        'duration': '2.0',
        'type': 'plenary',
    })

    # Should not get our specific validation error
    error_msg = ('You can only add attendance for yourself or your '
                 'commission members')
    assert error_msg not in str(page)


def test_commission_president_cannot_add_for_other_commission_members(client):
    '''Commission presidents should NOT be able to add attendance for members
    of other commissions'''
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

    education_member_id = education_member.id
    transaction.commit()

    client.login('finance.president@example.org', 'test')

    # Try to submit form for member of different commission
    page = client.post('/attendences/new', {
        'parliamentarian_id': str(education_member_id),
        'date': '2024-01-15',
        'duration': '2.0',
        'type': 'plenary',
    })

    # Should get validation error
    assert ('You can only add attendance for yourself or your commission '
            'members') in page
