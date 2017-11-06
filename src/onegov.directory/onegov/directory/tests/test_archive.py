import json
import pytest
import transaction

from datetime import date
from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryArchive
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
        {'Name': 'Evilcorp', 'Employees': 1000, 'Logo': None},
        {'Name': 'Initech', 'Employees': 250, 'Logo': 'logo/initech.png'}
    ]

    assert (temporary_path / 'logo/initech.png').is_file()
    assert not (temporary_path / 'logo/evilcorp.png').is_file()


@pytest.mark.parametrize('archive_format', ['json', 'csv'])
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
            return key, ', '.join(value)

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
