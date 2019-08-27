import pytest
import transaction

from io import BytesIO
from onegov.core.utils import Bunch
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryEntry
from onegov.directory import DirectoryEntryCollection
from onegov.directory.errors import DuplicateEntryError, ValidationError
from onegov.file import File


def test_directory_title_and_order(session):
    doctors = DirectoryCollection(session).add(
        title='Doctors',
        structure="""
            Name = ___
        """,
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
            title="[General/First Name] [General/Last Name]",
            order=('General/Last Name', 'General/First Name'),
        )
    )

    assert people.configuration.title\
        == "[General/First Name] [General/Last Name]"

    assert people.configuration.order == (
        'General/Last Name',
        'General/First Name'
    )

    person = {
        'general_first_name': 'Tom',
        'general_last_name': 'Riddle'
    }

    assert people.configuration.extract_title(person) == 'Tom Riddle'
    assert people.configuration.extract_order(person) == 'riddle-tom'

    people.configuration.title = "[General/Last Name] [General/First Name]"
    session.flush()

    people = DirectoryCollection(session).query().first()
    assert people.configuration.extract_title(person) == 'Riddle Tom'


def test_directory_configuration_missing_fields():
    cfg = DirectoryConfiguration(
        title="[First Name] [Last Name]",
        keywords=['Category']
    )

    assert not cfg.missing_fields("""
        First Name *= ___
        Last Name *= ___
        Category *=
            [ ] Consultant
            [ ] Employee
    """)

    assert cfg.missing_fields("""
        First Name *= ___
        Last Name *= ___
    """) == {'keywords': ['Category']}

    assert cfg.missing_fields("""
        First Name *= ___
        Category *=
            [ ] Consultant
            [ ] Employee
    """) == {'title': ['Last Name']}


def test_directory_form(session):
    people = DirectoryCollection(session).add(
        title='People',
        structure="""
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[First Name] [Last Name]",
            order=('Last Name', 'First Name'),
        )
    )

    form = people.form_class()
    form.first_name.data = 'Rick'
    form.last_name.data = 'Sanchez'

    rick = DirectoryEntry(content={})
    form.populate_obj(rick)

    assert rick.title == 'Rick Sanchez'
    assert rick.order == 'sanchez-rick'
    assert rick.values['first_name'] == 'Rick'
    assert rick.values['last_name'] == 'Sanchez'

    form = people.form_class()
    form.process(obj=rick)

    assert form.first_name.data == 'Rick'
    assert form.last_name.data == 'Sanchez'


def test_directory_entry_collection(session):
    directory = DirectoryCollection(session).add(
        title='Albums',
        structure="""
            Artist *= ___
            Title *= ___
            Year *= 1900..2100
            Genre =
                [ ] Hip Hop
                [ ] Pop
                [ ] Rock
            German =
                ( ) Yes
                ( ) No
        """,
        configuration=DirectoryConfiguration(
            title="[Title]",
            order=('Artist', 'Title'),
            keywords=('Genre', 'German')
        )
    )

    directory.add(values=dict(
        artist="Rise Against",
        title="Siren Song of the Counter-Culture",
        year=2004,
        genre=['Rock'],
        german='No'
    ))

    directory.add(values=dict(
        artist="Kettcar",
        title="Du und wieviel von deinen Freunden",
        year=2002,
        genre=['Rock', 'Pop'],
        german='Yes'
    ))

    directory.add(values=dict(
        artist="Hilltop Hoods",
        title="Drinking from the Sun, Walking Under Stars Restrung",
        year=2016,
        genre=['Hip Hop'],
        german='No'
    ))

    albums = DirectoryEntryCollection(directory)
    assert albums.query().count() == 3

    assert albums.for_filter(genre='Hip Hop').query().count() == 1
    assert albums.for_filter(genre='Hip Hop')\
        .for_filter(genre='Hip Hop').query().count() == 3

    assert albums.for_filter(genre='Rock').query().count() == 2
    assert albums.for_filter(genre='Rock')\
        .for_filter(genre='Pop').query().count() == 2

    kettcar = albums.for_filter(genre='Pop').query().one()
    assert kettcar.values == {
        'artist': 'Kettcar',
        'title': 'Du und wieviel von deinen Freunden',
        'year': 2002,
        'genre': ['Rock', 'Pop'],
        'german': 'Yes'
    }

    assert albums.for_filter(german='Yes').query().count() == 1
    assert albums.for_filter(
        german='Yes', singular=True
    ).for_filter(
        german='No', singular=True
    ).query().count() == 2

    assert albums.for_filter(
        german='Yes', singular=False
    ).for_filter(
        german='No', singular=False
    ).query().count() == 3

    # between categories, the filter is AND
    assert albums.for_filter(
        german='Yes'
    ).for_filter(
        genre='Rock'
    ).query().count() == 1


def test_validation_error(session):
    places = DirectoryCollection(session).add(
        title='Place',
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', ),
        )
    )

    with pytest.raises(ValidationError):
        places.add(values={'name': ''})


def test_files(session):
    press_releases = DirectoryCollection(session).add(
        title="Press Releases",
        structure="""
            Title *= ___
            File = *.txt
        """,
        configuration=DirectoryConfiguration(
            title=('Title', ),
            order=('Title', ),
        )
    )

    txt = Bunch(
        data=object(),
        file=BytesIO(b'just kidding'),
        filename='press-release.txt'
    )

    iphone_found = press_releases.add(values=dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        file=txt
    ))

    def commit():
        nonlocal iphone_found, press_releases

        transaction.commit()
        iphone_found = session.query(DirectoryEntry).one()
        press_releases = session.query(Directory).one()

    assert len(iphone_found.files) == 1
    assert iphone_found.values['file']['size'] == 12
    assert iphone_found.values['file']['mimetype'] == 'text/plain'
    assert iphone_found.values['file']['filename'] == 'press-release.txt'
    assert session.query(File).count() == 1

    file_id = session.query(File).one().id
    press_releases.update(iphone_found, dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        file=Bunch(data=None, action='keep')  # keep the file -> onegov.form
    ))
    commit()

    assert session.query(File).one().id == file_id

    press_releases.update(iphone_found, dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        file=Bunch(data={}, action='delete')  # delete the file -> onegov.form
    ))
    commit()

    assert session.query(File).count() == 0

    iphone_found = press_releases.update(iphone_found, values=dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        file=txt
    ))
    commit()

    assert session.query(File).count() == 1
    assert session.query(File).one().id != file_id

    # replacing the file leads to a new id
    file_id = session.query(File).one().id
    iphone_found = press_releases.update(iphone_found, values=dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        file=txt
    ))
    commit()

    assert session.query(File).one().id != file_id

    # deleting the model cascades to the session
    session.delete(iphone_found)
    session.flush()

    assert session.query(File).count() == 0


def test_migrate_text_field(session):
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
            Note  = ...
        """,
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', ),
        )
    )

    conference = rooms.add(values=dict(
        name="Conference Room",
        note="Has a beamer\nand snacks"
    ))

    rooms.structure = """
        Name *= ___
        Note  = ___
    """

    session.flush()
    assert conference.values['note'] == 'Has a beamer and snacks'


def test_migrate_rename_field(session):
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
            Note  = ___
        """,
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', ),
        )
    )

    conference = rooms.add(values=dict(
        name="Conference Room",
        note="Has a beamer and snacks"
    ))

    rooms.structure = """
        Name *= ___
        Notiz  = ___
    """

    session.flush()
    assert conference.values['notiz'] == 'Has a beamer and snacks'


def test_migrate_introduce_radio_field(session):
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', ),
        )
    )

    conference = rooms.add(values=dict(
        name="Conference Room",
        note="Has a beamer and snacks"
    ))

    rooms.structure = """
        Name *= ___
        Beamer =
            ( ) Yes
            ( ) No
    """

    session.flush()
    assert not conference.values['beamer']

    rooms.structure = """
        Name *= ___
        Beamer =
            (x) Yes
            ( ) No
    """

    session.flush()
    assert not conference.values['beamer'] == 'Yes'


def test_introduce_required_field_fail(session):
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', ),
        )
    )

    rooms.add(values=dict(
        name="Conference Room",
    ))

    rooms.structure = """
        Name *= ___
        Seats *= 0..99
    """

    with pytest.raises(ValidationError):
        session.flush()


def test_introduce_required_field(session):
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', ),
        )
    )

    conference = rooms.add(values=dict(
        name="Conference Room",
    ))

    # to introduce a new default field add it as optional
    rooms.structure = """
        Name *= ___
        Seats = 0..99
    """

    session.flush()

    # then fill out the values
    conference.values['seats'] = 3
    conference.content.changed()

    session.flush()

    # then mark it as required
    rooms.structure = """
        Name *= ___
        Seats *= 0..99
    """

    session.flush()


def test_introduce_image_field(session):
    logos = DirectoryCollection(session).add(
        title="Logos",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', )
        )
    )

    logos.add(values=dict(
        name="Mc Donalds"
    ))

    transaction.commit()

    logos = DirectoryCollection(session).query().one()
    assert logos.entries[0].values == {'name': 'Mc Donalds'}

    logos.structure = """
        Name *= ___
        Logo = *.jpg|*.png|*.gif
    """

    session.flush()
    assert logos.entries[0].values == {'name': 'Mc Donalds', 'logo': None}

    transaction.commit()

    logos = DirectoryCollection(session).query().one()
    assert logos.entries[0].values == {'name': 'Mc Donalds', 'logo': None}


def test_change_number_range_fail(session):
    rooms = DirectoryCollection(session).add(
        title="Prediction",
        structure="""
            Description *= ___
            Confidence = 0..1000
        """,
        configuration=DirectoryConfiguration(
            title=('Description', ),
            order=('Description', ),
        )
    )

    rooms.add(values=dict(
        description="Bitcoin is a Bubble",
        confidence=1000
    ))

    session.flush()

    rooms.structure = """
        Description *= ___
        Confidence = 0..100
    """

    with pytest.raises(ValidationError):
        session.flush()


def test_add_duplicate_entry(session):

    foos = DirectoryCollection(session).add(
        title="Foos",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title=('Name', ),
            order=('Name', ),
        )
    )

    foos.add(values=dict(name='foobar'))
    session.flush()

    with pytest.raises(DuplicateEntryError):
        foos.add(values=dict(name='foobar'))


def test_custom_order(session):

    names = DirectoryCollection(session).add(
        title="Names",
        structure="""
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title='[First Name] [Last Name]',
            order=('First Name', ),
        )
    )

    names.add(values=dict(first_name='Aaron', last_name='Zeebrox'))
    names.add(values=dict(first_name='Zora', last_name='Anderson'))

    session.flush()

    entries = DirectoryEntryCollection(names)

    names.configuration.order = ['First Name']
    names.configuration.direction = None
    assert [r.values['first_name'][0] for r in entries.query()] == ['A', 'Z']

    names.configuration.order = ['First Name']
    names.configuration.direction = 'asc'
    assert [r.values['first_name'][0] for r in entries.query()] == ['A', 'Z']

    names.configuration.order = ['Last Name']
    names.configuration.direction = 'asc'
    assert [r.values['first_name'][0] for r in entries.query()] == ['Z', 'A']

    names.configuration.order = ['Last Name']
    names.configuration.direction = 'desc'
    assert [r.values['first_name'][0] for r in entries.query()] == ['A', 'Z']
