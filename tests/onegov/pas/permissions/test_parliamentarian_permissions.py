from __future__ import annotations

import pytest
import transaction

from datetime import date
from morepath import Identity
from onegov.core.security import Private
from onegov.pas.collections import (
    PASCommissionCollection,
    PASParliamentarianCollection,
    SettlementRunCollection,
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
        email_primary='pia.parliamentarian@example.org',
        zg_username='zgpia',
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
    user = users.by_username('zgpia')
    assert user is not None
    user.password = 'test'
    user.role = 'parliamentarian'
    user.active = True

    transaction.commit()

    # Login as parliamentarian
    client.login('zgpia', 'test')

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
        email_primary='peter.president@example.org',
        zg_username='zgpeter',
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
    user = users.by_username('zgpeter')
    assert user is not None
    user.role = 'commission_president'
    user.password = 'test'
    user.active = True

    transaction.commit()

    # Login as commission president
    page = client.login('zgpeter', 'test')
    assert 'falsches Passwort' not in page

    # Should be able to access dashboard
    page = client.get('/pas-settings')
    assert page.status_code == 200


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
        email_primary='emma.president@example.org',
        zg_username='zgemma',
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
    user = users.by_username('zgemma')
    assert user is not None
    user.role = 'commission_president'
    user.password = 'test'
    user.active = True

    # Get the commission ID before committing
    commission_id = commission.id

    transaction.commit()

    # Login as commission president
    client.login('zgemma', 'test')

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
        email_primary='frank.president@example.org',
        zg_username='zgfrank',
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
    user = users.by_username('zgfrank')
    assert user is not None
    user.role = 'commission_president'

    transaction.commit()

    # Test permission rule with president identity
    identity = Identity(
        uid='foo',
        userid='zgfrank',
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
        email_primary='mary.member@example.org',
        zg_username='zgmary',
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
    user = users.by_username('zgmary')
    assert user is not None
    user.role = 'parliamentarian'

    transaction.commit()

    # Test permission rule with parliamentarian identity
    identity = Identity(
        uid='foo',
        userid='zgmary',
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
        email_primary='george.president@example.org',
        zg_username='zggeorge',
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
    user = users.by_username('zggeorge')
    assert user is not None
    user.role = 'commission_president'

    transaction.commit()

    # Test permission rule with president identity
    identity = Identity(
        uid='foo',
        userid='zggeorge',
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


@pytest.mark.parametrize('role,user_email,zg_user', [
    ('parliamentarian', 'files.parliamentarian@example.org',
     'zgfilesparl'),
    ('commission_president', 'files.president@example.org',
     'zgfilespres'),
])
def test_view_files_collection(
    client: Client[TestPasApp],
    role: str,
    user_email: str,
    zg_user: str,
) -> None:
    """Parliamentarians and commission presidents should be able to access
    the files collection"""
    session = client.app.session()

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Files',
        last_name='Viewer',
        email_primary=user_email,
        zg_username=zg_user,
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
    user = users.by_username(zg_user)
    assert user is not None
    user.role = role
    user.password = 'test'
    user.active = True
    transaction.commit()

    # Login as user
    client.login(zg_user, 'test')

    page = client.get('/files')
    assert page.status_code == 200


def test_parliamentarian_self_bookings_show_in_list(
    client: Client[TestPasApp],
) -> None:
    """Parliamentarian creates commission/shortest/study via form,
    all three must appear in /attendences list."""
    session = client.app.session()

    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Test Commission')

    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Parla',
        last_name='Mentarian',
        email_primary='parla.mentarian@example.org',
        zg_username='zgparla',
    )

    session.add(PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='member',
        start=date(2020, 1, 1),
    ))

    SettlementRunCollection(session).add(
        name='Active Run',
        start=date(2020, 1, 1),
        end=date(2099, 12, 31),
        active=True,
    )

    user = UserCollection(session).by_username('zgparla')
    assert user is not None
    user.password = 'test'
    user.role = 'parliamentarian'
    user.active = True
    transaction.commit()

    client.login('zgparla', 'test')

    for a_type in ('commission', 'shortest', 'study'):
        page = client.get('/attendences/new')
        page.form['date'] = date.today().isoformat()
        page.form['duration'] = '2.0'
        page.form['type'] = a_type
        page.form['parliamentarian_id'].select(text='Parla Mentarian')
        page.form['commission_id'].select(text='Test Commission')
        assert page.form.submit().maybe_follow().status_code == 200

    list_page = client.get('/attendences')
    for label in ('Kommissionsitzung', 'Kürzestsitzung', 'Aktenstudium'):
        assert label in list_page, f'{label} missing\n\n{list_page}'

    filtered = client.get('/attendences?type=study')
    assert 'Aktenstudium' in filtered
    assert 'Kürzestsitzung' not in filtered.pyquery('table.attendences').text()

    assert 'fa-edit' not in list_page


def test_parliamentarian_sees_add_link_but_not_bulk(
    client: Client[TestPasApp],
) -> None:
    """Parliamentarian sees 'New Attendence' in editbar but not
    bulk options, and no edit icons on rows."""
    session = client.app.session()

    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarians.add(
        first_name='Eva',
        last_name='Editbar',
        email_primary='eva.editbar@example.org',
        zg_username='zgeva',
    )

    user = UserCollection(session).by_username('zgeva')
    assert user is not None
    user.password = 'test'
    user.role = 'parliamentarian'
    user.active = True
    transaction.commit()

    client.login('zgeva', 'test')

    page = client.get('/attendences')
    editbar = page.pyquery('.edit-bar').text()
    assert 'Sitzung' in editbar
    assert 'Massenbuchung' not in editbar
