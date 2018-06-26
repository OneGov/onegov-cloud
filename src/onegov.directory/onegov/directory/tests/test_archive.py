import pytest
import transaction

from datetime import date
from onegov.core.custom import json
from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryArchive
from onegov.directory import DirectoryZipArchive
from onegov_testing.utils import create_image
from tempfile import NamedTemporaryFile


def test_archive_create(session, temporary_path):
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

    businesses = directories.by_name('businesses')

    archive = DirectoryArchive(temporary_path, 'json')
    archive.write(businesses)

    metadata = json.loads((temporary_path / 'metadata.json').open().read())
    data = json.loads((temporary_path / 'data.json').open().read())

    assert metadata['title'] == businesses.title
    assert metadata['lead'] == businesses.lead
    assert metadata['type'] == businesses.type
    assert metadata['structure'] == businesses.structure
    assert metadata['configuration'] == businesses.configuration.to_dict()
    assert data == [
        {
            'Name': 'Evilcorp',
            'Employees': 1000,
            'Logo': None,
            'Latitude': None,
            'Longitude': None,
        },
        {
            'Name': 'Initech',
            'Employees': 250,
            'Logo': 'logo/initech.png',
            'Latitude': None,
            'Longitude': None,
        }
    ]

    assert (temporary_path / 'logo/initech.png').is_file()
    assert not (temporary_path / 'logo/evilcorp.png').is_file()


@pytest.mark.parametrize('archive_format', ['json', 'csv', 'xlsx'])
def test_archive_import(session, temporary_path, archive_format):
    directories = DirectoryCollection(session)
    businesses = directories.add(
        title="Businesses",
        lead="The town's businesses",
        structure="""
            Name *= ___
            Employees = 0..1000
            Logo = *.png
            Founded = YYYY.MM.DD
            Sectors =
                [ ] IT
                [ ] SMB
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
        ),
        founded=date(2000, 1, 1),
        sectors=['IT', 'SMB']
    ))

    businesses.add(values=dict(
        name="Evilcorp",
        employees=1000,
        logo=None,
        founded=date(2014, 2, 3),
        sectors=['IT']
    ))

    transaction.commit()

    businesses = directories.by_name('businesses')

    def transform(key, value):
        if isinstance(value, date):
            return key, value.strftime('%d.%m.%Y')

        if isinstance(value, (list, tuple)):
            return key, '\n'.join(value)

        return key, value

    archive = DirectoryArchive(temporary_path, archive_format, transform)
    archive.write(businesses)

    read = archive.read()

    assert read.title == businesses.title
    assert read.lead == businesses.lead
    assert read.name == businesses.name
    assert read.type == businesses.type

    evilcorp, initech = read.entries
    assert evilcorp.name == 'evilcorp'
    assert evilcorp.title == 'Evilcorp'
    assert evilcorp.values['name'] == 'Evilcorp'
    assert evilcorp.values['employees'] == 1000
    assert evilcorp.values['founded'] == date(2014, 2, 3)
    assert evilcorp.values['sectors'] == ['IT']
    assert len(evilcorp.files) == 0

    assert initech.name == 'initech'
    assert initech.title == 'Initech'
    assert initech.values['name'] == 'Initech'
    assert initech.values['employees'] == 250
    assert initech.values['founded'] == date(2000, 1, 1)
    assert initech.values['sectors'] == ['IT', 'SMB']
    assert len(initech.files) == 1
    assert initech.files[0].name == 'initech.png'


def test_zip_archive_from_buffer(session, temporary_path):
    directories = DirectoryCollection(session)
    businesses = directories.add(
        title="Businesses",
        lead="The town's businesses",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    businesses.add(values=dict(name="Aesir Corp."))
    transaction.commit()

    businesses = directories.by_name('businesses')

    archive = DirectoryZipArchive(temporary_path / 'archive.zip', 'json')
    archive.write(businesses)

    archive = DirectoryZipArchive.from_buffer(
        (temporary_path / 'archive.zip').open('rb'))

    directory = archive.read()
    assert directory.title == "Businesses"
    assert directory.lead == "The town's businesses"
    assert directory.structure == "Name *= ___"
    assert len(directory.entries) == 1


def test_corodinates(session, temporary_path):
    directories = DirectoryCollection(session)
    points = directories.add(
        title="Points of interest",
        lead="You gotta see this!",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    sign = points.add(values=dict(name="Govikon Sign"))
    sign.content['coordinates'] = {'lat': 34.1341151, 'lon': -118.3215482}

    transaction.commit()

    archive = DirectoryArchive(temporary_path, 'json')
    archive.write(directories.by_name('points-of-interest'))

    directory = archive.read()
    assert directory.title == "Points of interest"
    assert directory.entries[0].content['coordinates'] == {
        'lat': 34.1341151,
        'lon': -118.3215482,
        'zoom': None
    }


def test_import_duplicates(session, temporary_path):
    directories = DirectoryCollection(session)
    foos = directories.add(
        title="Foos",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    bars = directories.add(
        title="Bars",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    bars.add(values=dict(name='foobar'))
    foos.add(values=dict(name='foobar'))

    session.flush()

    foo_path = temporary_path / 'foo'
    bar_path = temporary_path / 'bar'

    foo_path.mkdir()
    bar_path.mkdir()

    foo_archive = DirectoryArchive(foo_path, 'json')
    foo_archive.write(foos)

    bar_archive = DirectoryArchive(bar_path, 'json')
    bar_archive.write(bars)

    for entry in foos.entries:
        session.delete(entry)

    for entry in bars.entries:
        session.delete(entry)

    session.flush()

    foo_archive.read(foos)
    bar_archive.read(bars)
