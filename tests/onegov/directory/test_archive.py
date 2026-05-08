from __future__ import annotations

import shutil
from pathlib import Path
from unittest.mock import patch

import pytest
import transaction

from datetime import date
from onegov.core.custom import json
from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryEntryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryArchive
from onegov.directory import DirectoryZipArchive
from tests.shared.utils import create_image
from tempfile import NamedTemporaryFile


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_archive_create(session: Session, temporary_path: Path) -> None:
    directories = DirectoryCollection(session)
    businesses = directories.add(
        title="Businesses",
        lead="The town's businesses",
        structure="""
            Name *= ___
            Employees = 0..1000
            Logo = *.png
            Images = *.png (multiple)

        """,
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )

    logo = NamedTemporaryFile(suffix='.png')
    image1 = NamedTemporaryFile(suffix='.png')
    image2 = NamedTemporaryFile(suffix='.png')
    businesses.add(values=dict(
        name="Initech",
        employees=250,
        logo=Bunch(
            data=object(),
            file=create_image(output=logo).file,
            filename='logo.png'
        ),
        images=(
            Bunch(
                data=object(),
                file=create_image(output=image1).file,
                filename='image1.png'
            ),
            Bunch(
                data=object(),
                file=create_image(output=image2).file,
                filename='image2.png'
            ),
        )
    ))

    businesses.add(values=dict(
        name="Evilcorp",
        employees=1000,
        logo=None,
        images=()
    ))

    transaction.commit()

    businesses = directories.by_name('businesses')  # type: ignore[assignment]

    collection = DirectoryEntryCollection(businesses)
    query = collection.query().limit(1)

    archive = DirectoryArchive(temporary_path, 'json')

    with patch.object(archive, 'write_directory_entries',
                      return_value=None) as po:
        archive.write(businesses, query=query)
    po.assert_called_once_with(businesses, None, query)

    archive.write(businesses)

    metadata = json.loads((temporary_path / 'metadata.json').read_text())
    data = json.loads((temporary_path / 'data.json').read_text())

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
            'Images': None,
            'Latitude': None,
            'Longitude': None,
        },
        {
            'Name': 'Initech',
            'Employees': 250,
            'Logo': 'logo/initech.png',
            'Images': 'images/initech_1.png:images/initech_2.png',
            'Latitude': None,
            'Longitude': None,
        }
    ]

    assert (temporary_path / 'logo/initech.png').is_file()
    assert (temporary_path / 'images/initech_1.png').is_file()
    assert (temporary_path / 'images/initech_2.png').is_file()
    assert not (temporary_path / 'logo/evilcorp.png').is_file()
    assert not (temporary_path / 'images/evilcorp_1.png').is_file()


@pytest.mark.parametrize('archive_format', ['json', 'csv', 'xlsx'])
def test_archive_import(
    session: Session,
    temporary_path: Path,
    archive_format: Literal['json', 'csv', 'xlsx']
) -> None:

    directories = DirectoryCollection(session)
    businesses = directories.add(
        title="Businesses",
        lead="The town's businesses",
        structure="""
            Name *= ___
            Employees = 0..1000
            Logo = *.png
            Images = *.png (multiple)
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

    logo = NamedTemporaryFile(suffix='.png')
    image1 = NamedTemporaryFile(suffix='.png')
    image2 = NamedTemporaryFile(suffix='.png')
    businesses.add(values=dict(
        name="Initech",
        employees=250,
        logo=Bunch(
            data=object(),
            file=create_image(output=logo).file,
            filename='logo.png'
        ),
        images=(
            Bunch(
                data=object(),
                file=create_image(output=image1).file,
                filename='image1.png'
            ),
            Bunch(
                data=object(),
                file=create_image(output=image2).file,
                filename='image2.png'
            ),
        ),
        founded=date(2000, 1, 1),
        sectors=['IT', 'SMB']
    ))

    businesses.add(values=dict(
        name="Evilcorp",
        employees=1000,
        logo=None,
        images=(),
        founded=date(2014, 2, 3),
        sectors=['IT']
    ))

    transaction.commit()

    businesses = directories.by_name('businesses')  # type: ignore[assignment]

    def transform(key: str, value: object) -> tuple[str, object]:
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
    assert len(initech.files) == 3
    assert initech.files[0].name == 'initech.png'
    assert initech.files[1].name == 'initech_1.png'
    assert initech.files[2].name == 'initech_2.png'


def test_zip_archive_from_buffer(
    session: Session,
    temporary_path: Path
) -> None:

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

    businesses = directories.by_name('businesses')  # type: ignore[assignment]

    archive = DirectoryZipArchive(temporary_path / 'archive.zip', 'json')
    archive.write(businesses)

    archive = DirectoryZipArchive.from_buffer(
        (temporary_path / 'archive.zip').open('rb'))

    directory = archive.read()
    assert directory.title == "Businesses"
    assert directory.lead == "The town's businesses"
    assert directory.structure == "Name *= ___"
    assert len(directory.entries) == 1


@pytest.mark.parametrize('archive_format', ['json', 'csv', 'xlsx'])
def test_zip_archive_from_buffer_with_folder_in_zip(
    session: Session,
    temporary_path: Path,
    archive_format: Literal['json', 'csv', 'xlsx']
) -> None:

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

    businesses = directories.by_name('businesses')  # type: ignore[assignment]

    original_zip = temporary_path / 'archive.zip'
    archive = DirectoryZipArchive(original_zip, archive_format)
    archive.write(businesses)

    def create_new_zip_containing_directory(original_zip: Path) -> Path:
        """ Takes the zip and puts a top-level directory in it. """
        working_directory = temporary_path / "extracted"
        working_directory.mkdir(parents=True, exist_ok=True)
        shutil.unpack_archive(original_zip, extract_dir=working_directory)
        root_dir = temporary_path / "top"
        wrapper = root_dir / "container"
        shutil.copytree(working_directory, wrapper)
        zip_destination = str(temporary_path / 'archive_with_root')
        return Path(shutil.make_archive(zip_destination, "zip", root_dir))

    new_zip = create_new_zip_containing_directory(original_zip)

    archive = DirectoryZipArchive.from_buffer(new_zip.open('rb'))

    directory = archive.read()
    assert directory.title == "Businesses"
    assert directory.lead == "The town's businesses"
    assert directory.structure == "Name *= ___"
    assert len(directory.entries) == 1


def test_corodinates(session: Session, temporary_path: Path) -> None:
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

    points = directories.by_name('points-of-interest')  # type: ignore[assignment]
    archive = DirectoryArchive(temporary_path, 'json')
    archive.write(points)

    directory = archive.read()
    assert directory.title == "Points of interest"
    assert directory.entries[0].content['coordinates'] == {
        'lat': 34.1341151,
        'lon': -118.3215482,
        'zoom': None
    }


def test_import_duplicates(session: Session, temporary_path: Path) -> None:
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
