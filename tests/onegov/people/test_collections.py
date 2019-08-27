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
        order_within_agency=2,
        order_within_person=0
    )
    memberships.add(
        title="Director",
        agency_id=agency.id,
        person_id=tom.id,
        order_within_agency=1,
        order_within_person=1
    )

    assert [m.title for m in memberships.query('order_within_agency')] ==\
           ["Director", "Member"]


def test_memberships_move(session):
    people = PersonCollection(session)
    person = people.add(first_name='First', last_name='Name')

    agencies = AgencyCollection(session)
    agency = agencies.add_root(title="Agency")

    ms = AgencyMembershipCollection(session)
    ms_a = ms.add(
        title="A",
        agency_id=agency.id,
        person_id=person.id,
        order_within_agency=1,
        order_within_person=2
    )
    ms_b = ms.add(
        title="B",
        agency_id=agency.id,
        person_id=person.id,
        order_within_agency=2,
        order_within_person=1
    )
    ms_c = ms.add(
        title="C",
        agency_id=agency.id,
        person_id=person.id,
        order_within_agency=3,
        order_within_person=0
    )

    assert [m.title for m in ms.query(
        order_by='order_within_agency'
    )] == ['A', 'B', 'C']

    assert [m.title for m in ms.query(
        order_by='order_within_person'
    )] == ['C', 'B', 'A']

    ms.move(ms_a, ms_b, MoveDirection.below, 'order_within_agency')
    assert [m.title for m in ms.query('order_within_agency')] == \
           ['B', 'A', 'C']

    ms.move(ms_c, ms_b, MoveDirection.above, 'order_within_agency')
    assert [m.title for m in ms.query('order_within_agency')] == \
           ['C', 'B', 'A']

    ms.move(ms_b, ms_a, MoveDirection.below, 'order_within_person')
    assert [m.title for m in ms.query('order_within_person')] == \
           ['C', 'A', 'B']

    ms.move(ms_a, ms_c, MoveDirection.above, 'order_within_person')
    assert [m.title for m in ms.query('order_within_person')] == \
           ['A', 'C', 'B']
