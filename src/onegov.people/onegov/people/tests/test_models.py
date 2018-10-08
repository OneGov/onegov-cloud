from onegov.people import Person


def test_person_polymorphism(session):

    class MyPerson(Person):
        __mapper_args__ = {'polymorphic_identity': 'my'}

    class MyOtherPerson(Person):
        __mapper_args__ = {'polymorphic_identity': 'other'}

    session.add(Person(first_name='default', last_name='person'))
    session.add(MyPerson(first_name='my', last_name='person'))
    session.add(MyOtherPerson(first_name='other', last_name='person'))
    session.flush()

    assert session.query(Person).count() == 3
    assert session.query(MyPerson).one().first_name == 'my'
    assert session.query(MyOtherPerson).one().first_name == 'other'
