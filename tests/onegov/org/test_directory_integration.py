from tempfile import NamedTemporaryFile

import transaction

from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryConfiguration, \
    DirectoryZipArchive, DirectoryEntryCollection
from onegov.org.layout import DirectoryEntryCollectionLayout
from onegov.org.models import ExtendedDirectory


class DummyApp(object):

    def __init__(self, session, application_id='my-app'):
        self._session = session
        self.application_id = application_id
        self.org = Bunch(geo_provider='none')

    def session(self):
        return self._session


class DummyRequest:
    def __init__(self, session):

        self.session = session
        self.app = DummyApp(session)

    def include(self, name):
        pass

    @property
    def is_manager(self):
        return True


def test_directory_roundtrip(session, temporary_path):
    export_fmt = 'json'
    directories = DirectoryCollection(session, type='extended')
    dir_structure = "Name *= ___\nContact (for infos) = ___"
    events = directories.add(
        title="Events",
        lead="The town's events",
        structure=dir_structure,
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        ),
        meta={
            'enable_map': False,
            'enable_submission': False,
            'enable_change_requests': False,
            'payment_method': None,
        },
        content={
            'marker_color': 'red',

        }
    )

    events.add(values=dict(
        name="Dance",
        contact_for_infos_='John',

    ))
    transaction.commit()

    events = directories.by_name('events')

    archive = DirectoryZipArchive(temporary_path / 'archive.zip', export_fmt)
    archive.write(events)

    archive = DirectoryZipArchive.from_buffer(
        (temporary_path / 'archive.zip').open('rb'))

    directory = archive.read()
    assert directory.type == 'extended'
    assert isinstance(directory, ExtendedDirectory)

    assert directory.title == "Events"
    assert directory.lead == "The town's events"
    assert directory.structure == dir_structure
    assert directory.fields[1].id == 'contact_for_infos_'
    assert len(directory.entries) == 1

    # Now export as in view_zip_file in views

    def transform(key, value):
        return formatter(key), formatter(value)

    request = DummyRequest(session)
    self = DirectoryEntryCollection(directory, type='extended')
    layout = DirectoryEntryCollectionLayout(self, request)
    formatter = layout.export_formatter(export_fmt)

    with NamedTemporaryFile() as f:
        archive = DirectoryZipArchive(
            temporary_path / f'{f.name}.zip', export_fmt, transform)
        archive.write(self.directory)
