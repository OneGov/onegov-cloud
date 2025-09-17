from onegov.pas.collections import (
    AttendenceCollection,
    PASCommissionCollection
)
from onegov.pas.models import PASCommission
from onegov.pas.models import PASCommissionMembership
from onegov.pas.collections import PASParliamentarianCollection
from onegov.user import UserCollection
import transaction


def test_view_dashboard_as_parliamentarian(client):
    '''Parliamentarians should be able to access the dashboard'''
    session = client.app.session()

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Pia',
        last_name='Parliamentarian',
        email_primary='pia.parliamentarian@example.org'
    )

    # Set correct password for the created user
    users = UserCollection(session)
    user = users.by_username('pia.parliamentarian@example.org')
    user.password = 'test'

    transaction.commit()

    # Login as parliamentarian
    client.login('pia.parliamentarian@example.org', 'test')

    # Should be able to access dashboard
    page = client.get('/pas')
    assert page.status_code == 200
    # The page loads successfully - permission test passed!


def test_view_dashboard_as_commission_president(client):
    '''Commission presidents should be able to access the dashboard'''
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
    user.role = 'commission_president'

    transaction.commit()

    # Login as commission president
    client.login('peter.president@example.org', 'test')

    # Should be able to access dashboard
    page = client.get('/pas')
    assert page.status_code == 200
    assert 'Dashboard' in page


def test_view_attendences_as_parliamentarian(client):
    '''Parliamentarians should be able to view attendences'''
    session = client.app.session()
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Anna',
        last_name='Attendee',
        email_primary='anna.attendee@example.org'
    )
    transaction.commit()
    client.login('anna.attendee@example.org', 'test')
    page = client.get('/attendences')
    assert page.status_code == 200


def test_view_attendence_as_parliamentarian(client):
    '''Parliamentarians should be able to view individual attendences and
    create new ones'''
    session = client.app.session()

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Bob',
        last_name='Viewer',
        email_primary='bob.viewer@example.org'
    )

    # Create attendence
    attendences = AttendenceCollection(session)
    attendence = attendences.add(
        parliamentarian_id=parliamentarian.id,
        meeting_type='commission',
        status='present'
    )

    # Set correct password for the created user
    users = UserCollection(session)
    user = users.by_username('bob.viewer@example.org')
    user.password = 'test'

    transaction.commit()

    # Login as parliamentarian
    client.login('bob.viewer@example.org', 'test')

    # Should be able to view the attendence
    page = client.get(f'/attendence/{attendence.id}')
    assert page.status_code == 200

    # Should be able to access new attendance form
    page = client.get('/attendences/new')
    assert page.status_code == 200

    # Check if it's actually a form page (most important test)
    assert 'form' in page
    assert 'submit' in page.lower()

    # todo: claude
    # should be able to edit their own attendance


def test_view_commissions_as_parliamentarian(client):
    '''Parliamentarians should be able to view commissions'''
    session = client.app.session()

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Carol',
        last_name='Commissioner',
        email_primary='carol.commissioner@example.org'
    )
    transaction.commit()

    # Login as parliamentarian
    client.login('carol.commissioner@example.org', 'test')

    # Should be able to access commissions collection
    page = client.get('/commissions')
    assert page.status_code == 200


def test_view_commission_as_parliamentarian(client):
    '''Parliamentarians should be able to view individual commissions'''
    session = client.app.session()

    # Create commission
    commissions = PASCommissionCollection(session)
    commission = commissions.add(name='Finance Commission')

    # Create parliamentarian
    parliamentarians = PASParliamentarianCollection(client.app)
    parliamentarian = parliamentarians.add(
        first_name='Dave',
        last_name='Member',
        email_primary='dave.member@example.org'
    )

    # Make them commission member
    membership = PASCommissionMembership(
        parliamentarian_id=parliamentarian.id,
        commission_id=commission.id,
        role='member'
    )
    session.add(membership)
    transaction.commit()

    # Login as parliamentarian
    client.login('dave.member@example.org', 'test')

    # Should be able to view the commission
    page = client.get(f'/commission/{commission.id}')
    assert page.status_code == 200


def test_commission_president_has_private_access_to_commission(client):
    '''Commission presidents should have private access to their commissions'''
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
    user.role = 'commission_president'

    transaction.commit()

    # Login as commission president
    client.login('emma.president@example.org', 'test')

    # Should have private access to commission
    page = client.get(f'/commission/{commission.id}')
    assert page.status_code == 200


def test_commission_president_private_access_permission_rule(client):
    '''Test the has_private_access_to_commission permission rule directly'''
    from onegov.core.security import Private
    from onegov.pas.security import has_private_access_to_commission
    from morepath import Identity

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
    user.role = 'commission_president'

    transaction.commit()

    # Test permission rule with president identity
    identity = Identity(userid='frank.president@example.org',
                       role='commission_president')

    # Re-fetch commission from session to avoid detached instance issues
    fresh_commission = session.query(PASCommission).filter_by(
        name='Finance Commission').first()

    # Should have private access to their commission
    assert has_private_access_to_commission(
        client.app, identity, fresh_commission, Private
    ) is True


def test_parliamentarian_no_private_access_to_commission(client):
    '''Regular parliamentarians should not have private access to
    commissions'''
    from onegov.core.security import Private
    from onegov.pas.security import has_private_access_to_commission
    from morepath import Identity

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
    user.role = 'parliamentarian'

    transaction.commit()

    # Test permission rule with parliamentarian identity
    identity = Identity(
        userid='mary.member@example.org',
        role='parliamentarian'
    )

    # Should not have private access to commission
    assert has_private_access_to_commission(
        client.app, identity, commission, Private
    ) is False


def test_commission_president_no_access_to_different_commission(client):
    '''Commission presidents should not have private access to other
    commissions'''
    from onegov.core.security import Private
    from onegov.pas.security import has_private_access_to_commission
    from morepath import Identity

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
    user.role = 'commission_president'

    transaction.commit()

    # Test permission rule with president identity
    identity = Identity(userid='george.president@example.org',
                       role='commission_president')

    # Re-fetch commissions from session to avoid detached instance issues
    fresh_finance = session.query(PASCommission).filter_by(
        name='Finance Commission').first()
    fresh_education = session.query(PASCommission).filter_by(
        name='Education Commission').first()

    # Should have private access to their commission
    assert has_private_access_to_commission(
        client.app, identity, fresh_finance, Private
    ) is True

    # Should not have private access to different commission
    assert has_private_access_to_commission(
        client.app, identity, fresh_education, Private
    ) is False


def test_commission_president_with_no_parliamentarian_record(client):
    '''Commission presidents without parliamentarian record should not
    have access'''
    from onegov.core.security import Private
    from onegov.pas.security import has_private_access_to_commission
    from morepath import Identity

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
    identity = Identity(userid='orphan.president@example.org',
                       role='commission_president')

    # Should not have private access without parliamentarian record
    assert has_private_access_to_commission(
        client.app, identity, commission, Private
    ) is False
