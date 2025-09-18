from onegov.pas.collections import (
    AttendenceCollection,
    PASCommissionCollection,
    PASParliamentarianCollection
)
from onegov.pas.models import PASCommissionMembership
from onegov.user import UserCollection
import transaction
from datetime import date


def test_parliamentarian_can_edit_own_attendance(client):
    '''Parliamentarians should be able to edit their own attendance'''
    session = client.app.session()

    # Create parliamentarian A
    parliamentarians = PASParliamentarianCollection(client.app)
    parl_a = parliamentarians.add(
        first_name='Alice',
        last_name='Parliamentarian',
        email_primary='alice.parl@example.org'
    )

    # Set password for user A
    users = UserCollection(session)
    user_a = users.by_username('alice.parl@example.org')
    user_a.password = 'test'

    # Create attendance for parliamentarian A
    attendences = AttendenceCollection(session)
    attendance_a = attendences.add(
        parliamentarian_id=parl_a.id,
        type='commission',
        date=date.today(),
        duration=120
    )

    attendance_id_a = attendance_a.id
    transaction.commit()

    # Login as parliamentarian A
    client.login('alice.parl@example.org', 'test')

    # Should be able to edit their own attendance
    page = client.get(f'/attendence/{attendance_id_a}/edit')
    assert page.status_code == 200
    assert 'form' in page


def test_parliamentarian_cannot_edit_other_attendance(client):
    '''Parliamentarian A should NOT be able to edit parliamentarian B\'s
    attendance'''
    session = client.app.session()

    # Create parliamentarian A
    parliamentarians = PASParliamentarianCollection(client.app)
    parl_a = parliamentarians.add(
        first_name='Alice',
        last_name='Parliamentarian',
        email_primary='alice.parl@example.org'
    )

    # Create parliamentarian B
    parl_b = parliamentarians.add(
        first_name='Bob',
        last_name='Parliamentarian',
        email_primary='bob.parl@example.org'
    )

    # Set passwords
    users = UserCollection(session)
    user_a = users.by_username('alice.parl@example.org')
    user_a.password = 'test'
    user_b = users.by_username('bob.parl@example.org')
    user_b.password = 'test'

    # Create attendance for parliamentarian B
    attendences = AttendenceCollection(session)
    attendance_b = attendences.add(
        parliamentarian_id=parl_b.id,
        type='commission',
        date=date.today(),
        duration=90
    )

    attendance_id_b = attendance_b.id
    transaction.commit()

    # Login as parliamentarian A
    client.login('alice.parl@example.org', 'test')

    # Should NOT be able to edit parliamentarian B's attendance
    page = client.get(
        f'/attendence/{attendance_id_b}/edit', expect_errors=True
    )
    assert page.status_code in (403, 302)  # Forbidden or redirect

    # Should also NOT be able to view B's attendance details
    page = client.get(f'/attendence/{attendance_id_b}', expect_errors=True)
    assert page.status_code in (403, 302)


def test_commission_president_can_edit_member_attendance(client):
    '''Commission presidents should be able to edit attendance of their
    commission members'''
    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finance Commission')

    # Create commission president
    parliamentarians = PASParliamentarianCollection(client.app)
    president = parliamentarians.add(
        first_name='President',
        last_name='Leader',
        email_primary='president.leader@example.org'
    )

    # Create commission member
    member = parliamentarians.add(
        first_name='Member',
        last_name='Follower',
        email_primary='member.follower@example.org'
    )

    # Set up commission memberships
    president_membership = PASCommissionMembership(
        parliamentarian_id=president.id,
        commission_id=commission.id,
        role='president'
    )
    session.add(president_membership)

    member_membership = PASCommissionMembership(
        parliamentarian_id=member.id,
        commission_id=commission.id,
        role='member'
    )
    session.add(member_membership)

    # Set user roles and passwords
    users = UserCollection(session)
    president_user = users.by_username('president.leader@example.org')
    president_user.role = 'commission_president'
    president_user.password = 'test'

    member_user = users.by_username('member.follower@example.org')
    member_user.role = 'parliamentarian'
    member_user.password = 'test'

    # Create attendance for the member
    attendences = AttendenceCollection(session)
    member_attendance = attendences.add(
        parliamentarian_id=member.id,
        type='commission',
        date=date.today(),
        duration=180
    )

    attendance_id = member_attendance.id
    transaction.commit()

    # Login as commission president
    client.login('president.leader@example.org', 'test')

    # Should be able to edit member's attendance
    page = client.get(f'/attendence/{attendance_id}/edit')
    assert page.status_code == 200
    assert 'form' in page


def test_commission_president_cannot_edit_other_commission_attendance(client):
    '''Commission presidents should NOT be able to edit attendance of
    members from other commissions'''
    session = client.app.session()

    # Create two commissions
    commissions = PASCommissionCollection(session)
    finance_commission = commissions.add(name='Finance Commission')
    education_commission = commissions.add(name='Education Commission')

    # Create commission president of finance commission
    parliamentarians = PASParliamentarianCollection(client.app)
    finance_president = parliamentarians.add(
        first_name='Finance',
        last_name='President',
        email_primary='finance.president@example.org'
    )

    # Create member of education commission
    education_member = parliamentarians.add(
        first_name='Education',
        last_name='Member',
        email_primary='education.member@example.org'
    )

    # Set up commission memberships
    finance_membership = PASCommissionMembership(
        parliamentarian_id=finance_president.id,
        commission_id=finance_commission.id,
        role='president'
    )
    session.add(finance_membership)

    education_membership = PASCommissionMembership(
        parliamentarian_id=education_member.id,
        commission_id=education_commission.id,
        role='member'
    )
    session.add(education_membership)

    # Set user roles and passwords
    users = UserCollection(session)
    finance_user = users.by_username('finance.president@example.org')
    finance_user.role = 'commission_president'
    finance_user.password = 'test'

    education_user = users.by_username('education.member@example.org')
    education_user.role = 'parliamentarian'
    education_user.password = 'test'

    # Create attendance for education member
    attendences = AttendenceCollection(session)
    education_attendance = attendences.add(
        parliamentarian_id=education_member.id,
        type='commission',
        date=date.today(),
        duration=150
    )

    attendance_id = education_attendance.id
    transaction.commit()

    # Login as finance commission president
    client.login('finance.president@example.org', 'test')

    # Should NOT be able to edit education member's attendance
    page = client.get(f'/attendence/{attendance_id}/edit', expect_errors=True)
    assert page.status_code in (403, 302)


def test_parliamentarian_cannot_view_other_parliamentarian_details(client):
    '''Parliamentarians should not be able to view other
    parliamentarians\' personal details'''
    session = client.app.session()

    # Create parliamentarian A and B
    parliamentarians = PASParliamentarianCollection(client.app)
    parl_a = parliamentarians.add(
        first_name='Alice',
        last_name='Parliamentarian',
        email_primary='alice.parl@example.org'
    )

    parl_b = parliamentarians.add(
        first_name='Bob',
        last_name='Parliamentarian',
        email_primary='bob.parl@example.org'
    )

    # Set passwords
    users = UserCollection(session)
    user_a = users.by_username('alice.parl@example.org')
    user_a.password = 'test'
    user_b = users.by_username('bob.parl@example.org')
    user_b.password = 'test'

    parl_a_id = parl_a.id
    parl_b_id = parl_b.id
    transaction.commit()

    # Login as parliamentarian A
    client.login('alice.parl@example.org', 'test')

    # Should be able to view their own details
    page = client.get(f'/parliamentarian/{parl_a_id}')
    assert page.status_code == 200

    # Should NOT be able to view parliamentarian B's details
    page = client.get(f'/parliamentarian/{parl_b_id}', expect_errors=True)
    assert page.status_code in (403, 302)
