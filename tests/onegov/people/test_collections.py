from __future__ import annotations

from uuid import uuid4

from onegov.core.orm.abstract import MoveDirection
from onegov.people.collections import AgencyCollection
from onegov.people.collections import AgencyMembershipCollection
from onegov.people.collections import PersonCollection


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_people(session: Session) -> None:
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

    # try to add rachel again
    rachel_2 = people.add_or_get(
        first_name='Rachel',
        last_name='Scott',
        salutation='Dr.'
    )
    assert rachel_2 is rachel
    assert people.query().count() == 1

    # add Fritz twice with different email and phone
    fritz = people.add(
        first_name='Fritz',
        last_name='Fischer',
        email='fritz@teich.ch',
        phone='1234567890',
    )
    fritz_2 = people.add_or_get(
        first_name='Fritz',
        last_name='Fischer',
        email='fritz@lake.ch',
        phone='1234567891',
    )
    assert people.query().count() == 3
    assert fritz_2 is not fritz

    # add george twice option compare_names_only
    george = people.add(
        first_name='George',
        last_name='Washington',
        function='President'
    )
    george_2 = people.add_or_get(
        first_name='George',
        last_name='Washington',
        function='Founder',
        compare_names_only=True
    )
    assert people.query().count() == 4
    assert george_2 is george

    assert people.by_id(george.id) is george_2
    assert people.by_id('123') is None  # type: ignore[arg-type]
    assert people.by_id(uuid4()) is None


def test_agencies(session: Session) -> None:
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


def test_memberships(session: Session) -> None:
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

    assert [
        m.title
        for m in memberships.query('order_within_agency')
    ] == ["Director", "Member"]


def test_memberships_move(session: Session) -> None:
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
