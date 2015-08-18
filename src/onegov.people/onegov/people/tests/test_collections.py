from onegov.people import PersonCollection


def test_full_name(session):
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

    assert tom.title == 'Tom Chandler'
    assert rachel.title == 'Dr. Rachel Scott'
