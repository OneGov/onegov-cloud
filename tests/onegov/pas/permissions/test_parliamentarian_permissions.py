from __future__ import annotations

import pytest
import transaction

from datetime import date
from morepath import Identity
from onegov.core.security import Private
from onegov.pas.collections import (
    AttendenceCollection,
    PASCommissionCollection,
    PASParliamentarianCollection
)
from onegov.pas.models import PASCommission
from onegov.pas.models import PASCommissionMembership
from onegov.pas.security import has_private_access_to_commission
from onegov.user import UserCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.client import Client
    from ..conftest import TestPasApp


def test_view_dashboard_as_parliamentarian(client: Client[TestPasApp]) -> None:
    """Parliamentarians should be able to access the dashboard"""
    session = client.app.session()

    # Create commission for testing commission shortcuts
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Test Commission')

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Pia',
        last_name='Parliamentarian',
        email_primary='pia.parliamentarian@example.org'
    )

    # Add commission membership
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='member',
        start=date(2020, 1, 1)  # Active membership
    )
    session.add(membership)

    # Set correct password and role for the created user
    users = UserCollection(session)
    user = users.by_username('pia.parliamentarian@example.org')
    assert user is not None
    user.password = 'test'
    user.role = 'parliamentarian'

    transaction.commit()

    # Login as parliamentarian
    client.login('pia.parliamentarian@example.org', 'test')

    # Should be able to access dashboard
    page = client.get('/pas-settings')
    assert page.status_code == 200


def test_view_dashboard_as_commission_president(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents should be able to access the dashboard"""
    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Test Commission')

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Peter',
        last_name='President',
        email_primary='peter.president@example.org'
    )

    # Make them commission president
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='president'
    )
    session.add(membership)

    # Update user role to commission_president
    users = UserCollection(session)
    user = users.by_username('peter.president@example.org')
    assert user is not None
    user.role = 'commission_president'
    user.password = 'test'

    transaction.commit()

    # Login as commission president
    page = client.login('peter.president@example.org', 'test')
    assert 'falsches Passwort' not in page

    # Should be able to access dashboard
    page = client.get('/pas-settings')
    assert page.status_code == 200


def test_view_attendence_as_parliamentarian(
    client: Client[TestPasApp]
) -> None:
    """Parliamentarians should be able to view individual attendences and
    create new ones"""
    session = client.app.session()

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Bob',
        last_name='Viewer', email_primary='bob.viewer@example.org'
    )

    # Set correct password for the created user
    users = UserCollection(session)
    user = users.by_username('bob.viewer@example.org')
    assert user is not None
    user.password = 'test'

    # Create commission and add parliamentarian to it
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Test Commission')
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='member',
    )
    session.add(membership)

    # Create attendence
    attendences = AttendenceCollection(session)
    attendence = attendences.add(
        parliamentarian_id=parliamentarian.id,
        type='commission',
        date=date.today(),
        duration=120,
        commission_id=commission.id,
    )

    # Get the attendence ID before committing
    attendence_id = attendence.id
    transaction.commit()

    client.login('bob.viewer@example.org', 'test')
    # Should be able to view their own
    page = client.get(f'/attendence/{attendence_id}')
    assert page.status_code == 200

    # Should be able to access new attendance form
    # (that's the whole point of the app, really)
    page = client.get('/attendences/new')
    assert page.status_code == 200

    # Check if it's actually a form page (most important test)
    assert 'form' in page
    assert 'submit' in page

    # Should be able to edit their own attendance
    page = client.get(f'/attendence/{attendence_id}/edit').maybe_follow()
    assert page.status_code == 200

    # Fill out and submit the form
    page.form['date'] = '2024-01-15'
    page.form['duration'] = '3.5'
    page.form['type'] = 'study'
    page.form['parliamentarian_id'].select(text='Bob Viewer')

    # Submit the form
    page = page.form.submit().maybe_follow()
    assert page.status_code == 200


def test_parliamentarian_cannot_edit_others_attendence(
    client: Client[TestPasApp]
) -> None:
    """Parliamentarians should not be able to change parliamentarian_id
    when editing their own attendance"""
    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Test Commission')

    parliamentarians = PASParliamentarianCollection(client.app)
    alice = parliamentarians.add(
        first_name='Alice',
        last_name='One',
        email_primary='alice.one@example.org',
    )
    bob = parliamentarians.add(
        first_name='Bob', last_name='Two', email_primary='bob.two@example.org'
    )

    # Add alice to commission
    alice_membership = PASCommissionMembership(
        parliamentarian_id=alice.id, commission_id=commission.id, role='member'
    )
    session.add(alice_membership)

    users = UserCollection(session)
    alice_user = users.by_username('alice.one@example.org')
    assert alice_user is not None
    alice_user.password = 'test'
    alice_user.role = 'parliamentarian'

    attendences = AttendenceCollection(session)
    alice_attendence = attendences.add(
        parliamentarian_id=alice.id,
        type='commission',
        date=date.today(),
        duration=120,
        commission_id=commission.id,
    )

    alice_attendence_id = alice_attendence.id
    bob_id = str(bob.id)
    transaction.commit()

    client.login('alice.one@example.org', 'test')

    page = client.get(f'/attendence/{alice_attendence_id}/edit')
    assert page.status_code == 200

    page.form['date'] = '2024-01-15'
    page.form['duration'] = '3.5'
    page.form['type'] = 'commission'

    page.form['parliamentarian_id'].force_value(bob_id)

    page = page.form.submit()

    assert 'Sie können nur Ihre eigene Anwesenheit bearbeiten' in page


def test_commission_president_has_private_access_to_commission(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents should have private access to their commissions"""
    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Secret Commission')

    # Create parliamentarian as commission president
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Emma',
        last_name='President',
        email_primary='emma.president@example.org'
    )

    # Make them commission president
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='president'
    )
    session.add(membership)

    # Update user role to commission_president
    users = UserCollection(session)
    user = users.by_username('emma.president@example.org')
    assert user is not None
    user.role = 'commission_president'
    user.password = 'test'

    # Get the commission ID before committing
    commission_id = commission.id

    transaction.commit()

    # Login as commission president
    client.login('emma.president@example.org', 'test')

    # Should have private access to commission
    page = client.get(f'/commission/{commission_id}')
    assert page.status_code == 200


def test_commission_president_private_access_permission_rule(
    client: Client[TestPasApp]
) -> None:
    """Test the has_private_access_to_commission permission rule directly"""

    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finance Commission')

    # Create parliamentarian as commission president
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Frank',
        last_name='President',
        email_primary='frank.president@example.org'
    )

    # Make them commission president
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='president'
    )
    session.add(membership)

    # Update user role to commission_president
    users = UserCollection(session)
    user = users.by_username('frank.president@example.org')
    assert user is not None
    user.role = 'commission_president'

    transaction.commit()

    # Test permission rule with president identity
    identity = Identity(
        uid='foo',
        userid='frank.president@example.org',
        role='commission_president',
        application_id=client.app.application_id,
        groupids=frozenset()
    )

    # Re-fetch commission from session to avoid detached instance issues
    fresh_commission = session.query(PASCommission).filter_by(
        name='Finance Commission').first()
    assert fresh_commission is not None

    # Should have private access to their commission
    assert has_private_access_to_commission(
        client.app, identity, fresh_commission, Private
    ) is True


def test_parliamentarian_no_private_access_to_commission(
    client: Client[TestPasApp]
) -> None:
    """Regular parliamentarians should not have private access to
    commissions"""
    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finance Commission')

    # Create parliamentarian as regular member (not president)
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Mary',
        last_name='Member',
        email_primary='mary.member@example.org'
    )

    # Make them regular commission member
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='member'
    )
    session.add(membership)

    # Update user role to parliamentarian
    users = UserCollection(session)
    user = users.by_username('mary.member@example.org')
    assert user is not None
    user.role = 'parliamentarian'

    transaction.commit()

    # Test permission rule with parliamentarian identity
    identity = Identity(
        uid='foo',
        userid='mary.member@example.org',
        groupids=frozenset(),
        role='parliamentarian',
        application_id=client.app.application_id
    )

    # Should not have private access to commission
    assert has_private_access_to_commission(
        client.app, identity, commission, Private
    ) is False


def test_commission_president_no_access_to_different_commission(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents should not have private access to other
    commissions"""
    session = client.app.session()

    # Create two commissions
    commissions = PASCommissionCollection(session)
    finance_commission = commissions.add(name='Finance Commission')
    education_commission = commissions.add(name='Education Commission')

    # Create parliamentarian as president of finance commission
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='George',
        last_name='President',
        email_primary='george.president@example.org'
    )

    # Make them president of finance commission only
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=finance_commission.id,
        role='president'
    )
    session.add(membership)

    # Update user role to commission_president
    users = UserCollection(session)
    user = users.by_username('george.president@example.org')
    assert user is not None
    user.role = 'commission_president'

    transaction.commit()

    # Test permission rule with president identity
    identity = Identity(
        uid='foo',
        userid='george.president@example.org',
        groupids=frozenset(),
        role='commission_president',
        application_id=client.app.application_id
    )

    # Re-fetch commissions from session to avoid detached instance issues
    fresh_finance = session.query(PASCommission).filter_by(
        name='Finance Commission').first()
    assert fresh_finance is not None
    fresh_education = session.query(PASCommission).filter_by(
        name='Education Commission').first()
    assert fresh_education is not None

    # Should have private access to their commission
    assert has_private_access_to_commission(
        client.app, identity, fresh_finance, Private
    ) is True

    # Should not have private access to different commission
    assert has_private_access_to_commission(
        client.app, identity, fresh_education, Private
    ) is False


def test_commission_president_with_no_parliamentarian_record(
    client: Client[TestPasApp]
) -> None:
    """Commission presidents without parliamentarian record should not
    have access"""

    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finance Commission')

    # Create user with commission_president role but no parliamentarian record
    users = UserCollection(session)
    user = users.add(
        username='orphan.president@example.org',
        password='test',
        role='commission_president'
    )

    transaction.commit()

    # Test permission rule with president identity but no parliamentarian
    # record
    identity = Identity(
        uid='foo',
        userid='orphan.president@example.org',
        groupids=frozenset(),
        role='commission_president',
        application_id=client.app.application_id
    )

    # Should not have private access without parliamentarian record
    assert has_private_access_to_commission(
        client.app, identity, commission, Private
    ) is False


@pytest.mark.parametrize('role,user_email', [
    ('parliamentarian', 'files.parliamentarian@example.org'),
    ('commission_president', 'files.president@example.org'),
])
def test_view_files_collection(
    client: Client[TestPasApp],
    role: str,
    user_email: str
) -> None:
    """Parliamentarians and commission presidents should be able to access
    the files collection"""
    session = client.app.session()

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Files',
        last_name='Viewer',
        email_primary=user_email
    )

    if role == 'commission_president':
        # Create commission and make them president
        commissions = PASCommissionCollection(session)
        commission = commissions.add(name='File Commission')

        membership = PASCommissionMembership(
            parliamentarian_id=parliamentarian.id,
            commission_id=commission.id,
            role='president'
        )
        session.add(membership)

    # Set user role and password
    users = UserCollection(session)
    user = users.by_username(user_email)
    assert user is not None
    user.role = role
    user.password = 'test'
    transaction.commit()

    # Login as user
    client.login(user_email, 'test')

    page = client.get('/files')
    assert page.status_code == 200

    # TODO: Check disallow edit files for non admin
