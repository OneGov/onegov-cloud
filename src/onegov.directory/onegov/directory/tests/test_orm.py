from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryEntry


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
            # General
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title=('general_first_name', 'general_last_name'),
            order=('general_last_name', 'general_first_name'),
        )
    )

    assert people.configuration.title == (
        'general_first_name',
        'general_last_name'
    )
    assert people.configuration.order == (
        'general_last_name',
        'general_first_name'
    )

    person = {
        'general_first_name': 'Tom',
        'general_last_name': 'Riddle'
    }

    assert people.configuration.extract_title(person) == 'Tom Riddle'
    assert people.configuration.extract_order(person) == 'riddle-tom'

    people.configuration.title = ('general_last_name', 'general_first_name')
    session.flush()

    people = DirectoryCollection(session).query().first()
    assert people.configuration.extract_title(person) == 'Riddle Tom'


def test_directory_form(session):
    people = DirectoryCollection(session).add(
        title='People',
        structure="""
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title=('first_name', 'last_name'),
            order=('last_name', 'first_name'),
        )
    )

    form = people.form_class()
    form.first_name.data = 'Rick'
    form.last_name.data = 'Sanchez'

    rick = DirectoryEntry(content={})
    form.populate_obj(rick)

    assert rick.title == 'Rick Sanchez'
    assert rick.order == 'sanchez-rick'
    assert rick.content['fields']['first_name'] == 'Rick'
    assert rick.content['fields']['last_name'] == 'Sanchez'

    form = people.form_class()
    form.process(obj=rick)

    assert form.first_name.data == 'Rick'
    assert form.last_name.data == 'Sanchez'
