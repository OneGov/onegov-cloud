from onegov.org import (
    MembershipCollection,
    OrganizationCollection,
    PersonCollection
)


def test_simple_organization(session):
    organizations = OrganizationCollection(session)
    people = PersonCollection(session)
    memberships = MembershipCollection(session)

    ship = organizations.add_root('USS Nathan James')

    tom_chandler = people.add('Tom', 'Chandler')
    mike_slattery = people.add('Mike', 'Slattery')
    russ_jetter = people.add('Russ', 'Jeter')

    memberships.add_member(ship, tom_chandler, 'Commander')
    memberships.add_member(ship, mike_slattery, 'Executive Officer')
    memberships.add_member(ship, russ_jetter, 'Master Chief')

    assert len(ship.memberships) == 3
    assert len(tom_chandler.memberships) == 1
    assert len(mike_slattery.memberships) == 1
    assert len(russ_jetter.memberships) == 1

    assert tom_chandler.memberships[0].function == 'Commander'
    assert mike_slattery.memberships[0].function == 'Executive Officer'
    assert russ_jetter.memberships[0].function == 'Master Chief'
