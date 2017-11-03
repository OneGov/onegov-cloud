import json
import pytest
import transaction

from io import BytesIO
from onegov.core.utils import Bunch
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryEntry
from onegov.directory import DirectoryEntryCollection
from onegov.directory import DirectoryArchive
from onegov.directory.errors import ValidationError
from onegov.file import File
from onegov_testing.utils import create_image
from tempfile import NamedTemporaryFile


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
        """,
        configuration=DirectoryConfiguration(
            title="[Title]",
            order=('Artist', 'Title'),
            keywords=('Genre', )
        )
    )

    directory.add(values=dict(
        artist="Rise Against",
        title="Siren Song of the Counter-Culture",
        year=2004,
        genre=['Rock']
    ))

    directory.add(values=dict(
        artist="Kettcar",
        title="Du und wieviel von deinen Freunden",
        year=2002,
        genre=['Rock', 'Pop']
    ))

    directory.add(values=dict(
        artist="Hilltop Hoods",
        title="Drinking from the Sun, Walking Under Stars Restrung",
        year=2016,
        genre=['Hip Hop']
    ))

    albums = DirectoryEntryCollection(directory)
    assert albums.query().count() == 3

    assert albums.for_filter(genre='Hip Hop').query().count() == 1
    assert albums.for_filter(genre='Hip Hop')\
        .for_filter(genre='Hip Hop').query().count() == 3

    assert albums.for_filter(genre='Rock').query().count() == 2
    assert albums.for_filter(genre='Rock')\
        .for_filter(genre='Pop').query().count() == 1

    kettcar = albums.for_filter(genre='Pop').query().one()
    assert kettcar.values == {
        'artist': 'Kettcar',
        'title': 'Du und wieviel von deinen Freunden',
        'year': 2002,
        'genre': ['Rock', 'Pop']
    }


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
        file=Bunch(data=None)  # keep the file (from onegov.form)
    ))
    commit()

    assert session.query(File).one().id == file_id

    press_releases.update(iphone_found, dict(
        title="iPhone Found in Ancient Ruins in the Andes",
        file=Bunch(data={})  # delete the file (from onegov.form)
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


def test_archive(session, temporary_path):
    directories = DirectoryCollection(session)
    businesses = directories.add(
        title="Businesses",
        lead="The town's businesses",
        structure="""
            Name *= ___
            Employees = 0..1000
            Logo = *.png
        """,
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    output = NamedTemporaryFile(suffix='.png')
    businesses.add(values=dict(
        name="Initech",
        employees=250,
        logo=Bunch(
            data=object(),
            file=create_image(output=output).file,
            filename='logo.png'
        )
    ))

    businesses.add(values=dict(
        name="Evilcorp",
        employees=1000,
        logo=None
    ))

    transaction.commit()

    archive = DirectoryArchive(temporary_path, 'json')
    archive.write(directories.by_name('businesses'))

    metadata = json.loads((temporary_path / 'metadata.json').open().read())
    data = json.loads((temporary_path / 'data.json').open().read())

    assert metadata['title'] == businesses.title
    assert metadata['lead'] == businesses.lead
    assert metadata['type'] == businesses.type
    assert metadata['structure'] == businesses.structure
    assert metadata['configuration'] == businesses.configuration.to_dict()
    assert data == [
        {'Name': 'Evilcorp', 'Employees': 1000, 'Logo': None},
        {'Name': 'Initech', 'Employees': 250, 'Logo': 'logo/initech.png'}
    ]

    assert (temporary_path / 'logo/initech.png').is_file()
    assert not (temporary_path / 'logo/evilcorp.png').is_file()
