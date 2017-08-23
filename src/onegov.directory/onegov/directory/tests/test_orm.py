from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration


def test_directory_title_and_order(session):
    doctors = DirectoryCollection(session).add(
        title='Doctors',
        structure='',
        configuration=DirectoryConfiguration()
    )

    assert doctors.name == 'doctors'
    assert doctors.order == 'doctors'

    doctors.title = "General Practicioners"
    session.flush()

    assert doctors.name == 'doctors'
    assert doctors.order == 'general-practicioners'


def test_directory_fields(session):
    people = DirectoryCollection(session).add(
        title='People',
        structure="""
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration()
    )

    assert len(people.fields) == 2
    assert people.fields[0].label == 'First Name'
    assert people.fields[0].type == 'text'
    assert people.fields[0].required
    assert people.fields[1].label == 'Last Name'
    assert people.fields[1].type == 'text'
    assert people.fields[1].required


def test_directory_configuration(session):
    people = DirectoryCollection(session).add(
        title='People',
        structure="""
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title=('First Name', 'Last Name'),
            order=('Last Name', 'First Name'),
        )
    )

    assert people.configuration.title == ('First Name', 'Last Name')
    assert people.configuration.order == ('Last Name', 'First Name')

    person = {
        'First Name': 'Tom',
        'Last Name': 'Riddle'
    }

    assert people.configuration.extract_title(person) == 'Tom Riddle'
    assert people.configuration.extract_order(person) == 'riddle-tom'

    people.configuration.title = ('Last Name', 'First Name')
    session.flush()

    people = DirectoryCollection(session).query().first()
    assert people.configuration.extract_title(person) == 'Riddle Tom'
