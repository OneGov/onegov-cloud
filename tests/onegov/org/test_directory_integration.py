from tempfile import NamedTemporaryFile

import pytest
import transaction

from onegov.core.utils import Bunch
from onegov.directory import DirectoryCollection, DirectoryConfiguration, \
    DirectoryZipArchive, DirectoryEntryCollection
from onegov.directory.errors import DuplicateEntryError
from onegov.org.forms import DirectoryImportForm
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


@pytest.mark.parametrize('export_fmt,clear', [
    ('csv', True),
    ('csv', False),
    ('xlsx', True),
    ('xlsx', False),
    ('json', False),
    ('json', True),
])
def test_directory_roundtrip(
        session, temporary_path, export_fmt, clear):
    directories = DirectoryCollection(session, type='extended')
    dir_structure = """
            Name *= ___
            Contact (for infos) = ___
            Category =
                [ ] A
                [ ] B &;
                [ ] Z: with semicolon
            Choice =
                (x) yes
                ( ) no
            Notes = <markdown>
            Prozent = 0.00..100.00
        """
    events = directories.add(
        title="Events",
        lead="The town's events",
        structure=dir_structure,
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name'],
            keywords=['Category', 'Choice']
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
        category=['Z: with semicolon', 'B &;'],
        choice='no',
        notes=None,
        prozent=99

    ))
    events.add(values=dict(
        name="Zumba",
        contact_for_infos_='Helen',
        category=['A'],
        choice='yes',
        notes=None,
        prozent=99

    ))
    transaction.commit()

    events = directories.by_name('events')

    request = DummyRequest(session)
    self = DirectoryEntryCollection(events, type='extended')
    layout = DirectoryEntryCollectionLayout(self, request)
    formatter = layout.export_formatter(export_fmt)

    def transform(key, value):
        return formatter(key), formatter(value)

    with NamedTemporaryFile() as f:
        archive = DirectoryZipArchive(
            temporary_path / f'{f.name}.zip', export_fmt, transform)
        archive.write(self.directory)

    archive = DirectoryZipArchive.from_buffer(
        (temporary_path / f'{f.name}.zip').open('rb'))

    count = 0

    def count_entry(entry):
        nonlocal count
        count += 1

    # # Test add only new ones
    read_directory = archive.read(
        target=events,
        skip_existing=True,
        apply_metadata=False,
        after_import=count_entry
    )
    assert count == 0
    # Even though the metadata is not applied, the correct polymorphic class
    # has been loaded using the metadata. So the type gets always applied.
    assert read_directory.type == 'extended'

    if clear:
        DirectoryImportForm.clear_entries(session, events)

    directory = archive.read(
        target=events,
        skip_existing=True,
        apply_metadata=True,
        after_import=count_entry
    )

    if clear:
        assert count == 2
        assert directory.meta == events.meta
        assert directory.configuration == events.configuration
        assert directory.content == events.content
    else:
        assert count == 0

