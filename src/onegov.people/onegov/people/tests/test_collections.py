from onegov.people import AgencyCollection
from onegov.people import PersonCollection


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
