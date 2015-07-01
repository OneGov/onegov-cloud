import pytest

from onegov.org import (
    MembershipCollection,
    OrganizationCollection,
    PersonCollection
)
from sqlalchemy import exc


def test_simple_organization(session):
    organizations = OrganizationCollection(session)
    people = PersonCollection(session)
    memberships = MembershipCollection(session)

    ship = organizations.add_root('USS Nathan James')

    tom_chandler = people.add('Tom', 'Chandler')
    mike_slattery = people.add('Mike', 'Slattery')
    russ_jetter = people.add('Russ', 'Jeter')

    memberships.add(ship, tom_chandler, 'Commander')
    memberships.add(ship, mike_slattery, 'Executive Officer')
    memberships.add(ship, russ_jetter, 'Master Chief')

    assert len(ship.memberships) == 3
    assert len(tom_chandler.memberships) == 1
    assert len(mike_slattery.memberships) == 1
    assert len(russ_jetter.memberships) == 1

    assert tom_chandler.memberships[0].function == 'Commander'
    assert mike_slattery.memberships[0].function == 'Executive Officer'
    assert russ_jetter.memberships[0].function == 'Master Chief'


def test_membership_unique(session):
    organizations = OrganizationCollection(session)
    people = PersonCollection(session)
    memberships = MembershipCollection(session)

    whitehouse = organizations.add_root('The White House')

    barack_obama = people.add('Barack', 'Obama')

    memberships.add(whitehouse, barack_obama, 'President')

    with pytest.raises(exc.IntegrityError):
        memberships.add(whitehouse, barack_obama, 'Vice President')
