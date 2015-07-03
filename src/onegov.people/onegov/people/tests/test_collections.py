from onegov.people import PersonCollection


def test_full_name(session):
    people = PersonCollection(session)
    tom = people.add('Tom', 'Chandler')
    rachel = people.add('Rachel', 'Scott', academic_title='Dr.')

    assert tom.title == 'Tom Chandler'
    assert rachel.title == 'Dr. Rachel Scott'


def test_gravatar_url(session):
    people = PersonCollection(session)
    bill_gates = people.add('Bill', 'Gates', email='billg@microsoft.com')

    assert bill_gates.gravatar_url \
        == 'https://www.gravatar.com/avatar/2aa8acce7d935c5dd7f92e8871423bab'
