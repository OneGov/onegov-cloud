from onegov.core.orm.abstract import MoveDirection
from onegov.people.collections import AgencyCollection
from onegov.people.collections import AgencyMembershipCollection
from onegov.people.collections import PersonCollection


def test_people(session):
    people = PersonCollection(session)

    tom = people.add(
        first_name='Tom',
        last_name='Chandler'
    )
    rachel = people.add(
        first_name='Rachel',
        last_name='Scott',
        salutation='Dr.'
    )

    assert people.query().count() == 2
    assert people.by_id(rachel.id) == rachel

    people.delete(tom)
    assert people.query().count() == 1


def test_agencies(session):
    agencies = AgencyCollection(session)
    root = agencies.add_root(
        title="Root Agency"
    )
    child = agencies.add(
        title="Child Agency",
        parent=root
    )

    assert agencies.roots == [root]
    assert agencies.roots[0].children == [child]


def test_memberships(session):
    people = PersonCollection(session)
    tom = people.add(
        first_name='Tom',
        last_name='Chandler'
    )

    agencies = AgencyCollection(session)
    agency = agencies.add_root(
        title="Agency"
    )

    memberships = AgencyMembershipCollection(session)
    memberships.add(
        title="Member",
        agency_id=agency.id,
        person_id=tom.id,
        order=2
    )
    memberships.add(
        title="Director",
        agency_id=agency.id,
        person_id=tom.id,
        order=1
    )

    assert [m.title for m in memberships.query()] == ["Director", "Member"]


def test_memberships_move(session):
    people = PersonCollection(session)
    person = people.add(first_name='First', last_name='Name')

    agencies = AgencyCollection(session)
    agency = agencies.add_root(title="Agency")

    memberships = AgencyMembershipCollection(session)
    membership_a = memberships.add(
        title="A",
        agency_id=agency.id,
        person_id=person.id,
        order=1
    )
    membership_b = memberships.add(
        title="B",
        agency_id=agency.id,
        person_id=person.id,
        order=2
    )
    membership_c = memberships.add(
        title="C",
        agency_id=agency.id,
        person_id=person.id,
        order=3
    )

    assert [m.title for m in memberships.query()] == ['A', 'B', 'C']

    memberships.move(membership_a, membership_b, MoveDirection.below)
    assert [m.title for m in memberships.query()] == ['B', 'A', 'C']

    memberships.move(membership_c, membership_b, MoveDirection.above)
    assert [m.title for m in memberships.query()] == ['C', 'B', 'A']
