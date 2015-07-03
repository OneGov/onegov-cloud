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
        academic_title='Dr.'
    )

    assert tom.title == 'Tom Chandler'
    assert rachel.title == 'Dr. Rachel Scott'


def test_gravatar_url(session):
    people = PersonCollection(session)

    bill_gates = people.add(
        first_name='Bill',
        last_name='Gates',
        email='billg@microsoft.com'
    )

    assert bill_gates.gravatar_url \
        == 'https://www.gravatar.com/avatar/f9b0137cb32be76e5a171bff7ce98da7'
