from __future__ import annotations

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
from wtforms.validators import ValidationError as WtfValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_directory_title_and_order(session: Session) -> None:
    collection = DirectoryCollection(session)
    doctors = collection.add(
        title='Doctors',
        structure="""
            Name = ___
        """,
        configuration=DirectoryConfiguration()
    )

    patients = collection.add(
        title='Patients',
        structure="""
            Name = ___
        """,
        configuration=DirectoryConfiguration()
    )

    staff = collection.add(
        title='Staff',
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

    assert collection.query().all() == [doctors, patients, staff]


def test_directory_fields(session: Session) -> None:
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


def test_directory_configuration(session: Session) -> None:
    people = DirectoryCollection(session).add(
        title='People',
        structure="""
            # General
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[General/First Name] [General/Last Name]",
            order=['General/Last Name', 'General/First Name'],
        )
    )

    assert people.configuration.title\
        == "[General/First Name] [General/Last Name]"

    assert people.configuration.order == [
        'General/Last Name',
        'General/First Name'
    ]

    person = {
        'general_first_name': 'Tom',
        'general_last_name': 'Riddle'
    }

    assert people.configuration.extract_title(person) == 'Tom Riddle'
    assert people.configuration.extract_order(person) == 'riddle-tom'

    people.configuration.title = "[General/Last Name] [General/First Name]"
    session.flush()

    people = DirectoryCollection(session).query().first()  # type: ignore[assignment]
    assert people.configuration.extract_title(person) == 'Riddle Tom'


def test_directory_configuration_missing_fields() -> None:
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


def test_directory_form(session: Session) -> None:
    people = DirectoryCollection(session).add(
        title='People',
        structure="""
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title="[First Name] [Last Name]",
            order=['Last Name', 'First Name'],
        )
    )

    form = people.form_class()
    form['first_name'].data = 'Rick'
    form['last_name'].data = 'Sanchez'

    rick = DirectoryEntry(content={})
    form.populate_obj(rick)

    assert rick.title == 'Rick Sanchez'
    assert rick.order == 'sanchez-rick'
    assert rick.values['first_name'] == 'Rick'
    assert rick.values['last_name'] == 'Sanchez'

    form = people.form_class()
    form.process(obj=rick)

    assert form['first_name'].data == 'Rick'
    assert form['last_name'].data == 'Sanchez'


def test_directory_entry_collection(session: Session) -> None:
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
                [ ] Funk
            German =
                ( ) Yes
                ( ) No
        """,
        configuration=DirectoryConfiguration(
            title="[Title]",
            order=['Artist', 'Title'],
            keywords=['Genre', 'German']
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

    assert albums.for_toggled_keyword_value(
        'genre', 'Hip Hop'
    ).query().count() == 1
    assert albums.for_toggled_keyword_value(
        'genre', 'Hip Hop'
    ).for_toggled_keyword_value(
        'genre', 'Hip Hop'
    ).query().count() == 3

    assert albums.for_toggled_keyword_value(
        'genre', 'Rock'
    ).query().count() == 2
    assert albums.for_toggled_keyword_value(
        'genre', 'Rock'
    ).for_toggled_keyword_value(
        'genre', 'Pop'
    ).query().count() == 2

    kettcar = albums.for_toggled_keyword_value('genre', 'Pop').query().one()
    assert kettcar.values == {
        'artist': 'Kettcar',
        'title': 'Du und wieviel von deinen Freunden',
        'year': 2002,
        'genre': ['Rock', 'Pop'],
        'german': 'Yes'
    }

    assert albums.for_toggled_keyword_value(
        'german', 'Yes'
    ).query().count() == 1
    assert albums.for_toggled_keyword_value(
        'german', 'Yes', singular=True
    ).for_toggled_keyword_value(
        'german', 'No', singular=True
    ).query().count() == 2

    assert albums.for_toggled_keyword_value(
        'german', 'Yes', singular=False
    ).for_toggled_keyword_value(
        'german', 'No', singular=False
    ).query().count() == 3

    # between categories, the filter is AND
    assert albums.for_toggled_keyword_value(
        'german', 'Yes'
    ).for_toggled_keyword_value(
        'genre', 'Rock'
    ).query().count() == 1

    # test ordering
    sorted_entries = sorted(
        directory.entries, key=lambda en: en.order, reverse=True)

    assert directory.entries == sorted_entries
    assert albums.query().all() != sorted_entries


def test_validation_error(session: Session) -> None:
    places = DirectoryCollection(session).add(
        title='Place',
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
        )
    )

    with pytest.raises(ValidationError):
        places.add(values={'name': ''})


def test_files(session: Session) -> None:
    press_releases = DirectoryCollection(session).add(
        title="Press Releases",
        structure="""
            Title *= ___
            File = *.txt
        """,
        configuration=DirectoryConfiguration(
            title='Title',
            order=['Title'],
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

    def commit() -> None:
        nonlocal iphone_found, press_releases

        transaction.commit()
        iphone_found = session.query(DirectoryEntry).one()
        press_releases = session.query(Directory).one()

    assert len(iphone_found.files) == 1
    assert iphone_found.values['file']['size'] == 12
    assert iphone_found.values['file']['mimetype'] == 'text/plain'
    assert iphone_found.values['file']['filename'] == 'press-release.txt'
    assert session.query(File).count() == 1

    file = session.query(File).one()
    assert file.directory_entry == iphone_found  # type: ignore[attr-defined]
    file_id = file.id
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


def test_multi_files(session: Session) -> None:
    press_releases = DirectoryCollection(session).add(
        title="Press Releases",
        structure="""
            Title *= ___
            Files = *.txt (multiple)
        """,
        configuration=DirectoryConfiguration(
            title='Title',
            order=['Title'],
        )
    )

    txts = (
        Bunch(
            data=object(),
            file=BytesIO(b'just kidding'),
            filename='press-release.txt'
        ),
        Bunch(
            data=object(),
            file=BytesIO(b'no really'),
            filename='press-release-2.txt'
        ),
    )

    iphone_found = press_releases.add(values=dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        files=txts
    ))

    def commit() -> None:
        nonlocal iphone_found, press_releases

        transaction.commit()
        iphone_found = session.query(DirectoryEntry).one()
        press_releases = session.query(Directory).one()

    assert len(iphone_found.files) == 2
    assert iphone_found.values['files'][0]['size'] == 12
    assert iphone_found.values['files'][0]['mimetype'] == 'text/plain'
    assert iphone_found.values['files'][0]['filename'] == 'press-release.txt'
    assert iphone_found.values['files'][1]['size'] == 9
    assert iphone_found.values['files'][1]['mimetype'] == 'text/plain'
    assert iphone_found.values['files'][1]['filename'] == 'press-release-2.txt'
    assert session.query(File).count() == 2

    files = session.query(File).all()
    assert files[0].note == 'files:0'
    assert files[1].note == 'files:1'
    file1_id = files[0].id
    file2_id = files[1].id
    press_releases.update(iphone_found, dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        files=(
            # delte the first file -> onegov.form
            Bunch(data={}, action='delete'),
            # keep the second file -> onegov.form
            Bunch(data=None, action='keep')
        )
    ))
    commit()

    assert session.query(File).count() == 1
    new_file_1 = session.query(File).one()
    # the note should have been updated
    assert new_file_1.note == 'files:0'
    assert new_file_1.id == file2_id

    iphone_found = press_releases.update(iphone_found, values=dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        files=txts
    ))
    commit()

    assert session.query(File).count() == 2
    files = session.query(File).all()
    # neither of the files should be the original, because neither
    # had a `keep` action.
    assert files[0].note == 'files:0'
    assert files[0].id != file1_id
    assert files[1].note == 'files:1'
    assert files[1].id != file2_id

    # deleting the model cascades to the session
    session.delete(iphone_found)
    session.flush()

    assert session.query(File).count() == 0


def test_migrate_text_field(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
            Note  = ...
        """,
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
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


def test_migrate_rename_field(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
            Note  = ___
        """,
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
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


def test_migrate_introduce_radio_field(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
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


def test_introduce_required_field_fail(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
        )
    )

    rooms.add(values=dict(
        name="Conference Room",
    ))

    rooms.structure = """
        Name *= ___
        Seats *= 0..99
    """

    with pytest.raises((ValidationError, WtfValidationError)):
        session.flush()


def test_introduce_required_field(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title="Rooms",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
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
    conference.content.changed()  # type: ignore[attr-defined]

    session.flush()

    # then mark it as required
    rooms.structure = """
        Name *= ___
        Seats *= 0..99
    """

    session.flush()


def test_introduce_image_field(session: Session) -> None:
    logos = DirectoryCollection(session).add(
        title="Logos",
        structure="""
            Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
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


def test_change_number_range_fail(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title="Prediction",
        structure="""
            Description *= ___
            Confidence = 0..1000
        """,
        configuration=DirectoryConfiguration(
            title='Description',
            order=['Description'],
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


def test_add_duplicate_entry(session: Session) -> None:

    foos = DirectoryCollection(session).add(
        title="Foos",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title='Name',
            order=['Name'],
        )
    )

    foos.add(values=dict(name='foobar'))
    session.flush()

    with pytest.raises(DuplicateEntryError):
        foos.add(values=dict(name='foobar'))


def test_custom_order(session: Session) -> None:

    names = DirectoryCollection(session).add(
        title="Names",
        structure="""
            First Name *= ___
            Last Name *= ___
        """,
        configuration=DirectoryConfiguration(
            title='[First Name] [Last Name]',
            order=['First Name'],
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
