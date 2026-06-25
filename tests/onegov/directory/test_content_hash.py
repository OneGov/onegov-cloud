from __future__ import annotations

import transaction

from datetime import datetime, timezone
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.core.upgrade import UpgradeContext
from onegov.core.utils import Bunch
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryEntry
from onegov.directory.models.directory import DirectoryFile
from onegov.directory.upgrade import calc_content_hash_for_directory_entries
from onegov.file.utils import as_fileintent
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# --- Algorithm ---


def test_content_hash_on_create(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room'))

    assert conference.content_hash is not None
    assert len(conference.content_hash) == 40  # SHA-1 hex digest


def test_content_hash_is_deterministic(session: Session) -> None:
    # Calling update_content_hash() repeatedly must yield the same value.
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    first_hash = conference.content_hash
    assert first_hash is not None

    conference.update_content_hash()
    assert conference.content_hash == first_hash


def test_content_hash_independent_of_key_order(session: Session) -> None:
    # Hash must be the same regardless of dict key insertion order.
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="""
            Name *= ___
            Note = ___
        """,
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    entry1 = rooms.add(values=dict(name='A', note='B'))
    entry2 = rooms.add(values=dict(note='B', name='A'))

    assert entry1.content_hash == entry2.content_hash


# --- Via Directory.update() ---


def test_content_hash_changes_on_update(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="""
            Name *= ___
            Note = ___
        """,
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room', note='Nice'))
    original_hash = conference.content_hash
    assert original_hash is not None

    rooms.update(conference, dict(name='Conference Room', note='Even nicer'))

    assert conference.content_hash != original_hash


def test_content_hash_stable_when_no_change(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    original_hash = conference.content_hash

    rooms.update(conference, dict(name='Conference Room'))

    assert conference.content_hash == original_hash


def test_content_hash_changes_with_file(session: Session) -> None:
    press_releases = DirectoryCollection(session).add(
        title='Press Releases',
        structure="""
            Title *= ___
            File = *.txt
        """,
        configuration=DirectoryConfiguration(title='Title', order=['Title']),
    )

    txt = Bunch(
        data=object(), file=BytesIO(b'original content'), filename='report.txt'
    )

    entry = press_releases.add(values=dict(title='Annual Report', file=txt))

    def commit() -> None:
        nonlocal entry, press_releases
        transaction.commit()
        entry = session.query(DirectoryEntry).one()
        press_releases = session.query(Directory).one()

    hash_with_file = entry.content_hash
    assert hash_with_file is not None

    # remove the file — hash must change
    press_releases.update(
        entry,
        dict(title='Annual Report', file=Bunch(data={}, action='delete')),
    )
    commit()

    assert entry.content_hash != hash_with_file

    # add a new file — hash must change again
    txt2 = Bunch(
        data=object(),
        file=BytesIO(b'updated content'),
        filename='report-v2.txt',
    )
    press_releases.update(entry, dict(title='Annual Report', file=txt2))
    commit()

    assert entry.content_hash != hash_with_file


# --- Via observer (direct mutations, bypassing Directory.update) ---


def test_content_hash_updated_by_observer(session: Session) -> None:
    # Verifies the observer fires when values are set directly, without
    # going through Directory.update(). Exception: in-place mutation of the
    # inner dict bypasses the observer — see
    # test_inplace_values_mutation_does_not_update_hash.
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    original_hash = conference.content_hash
    assert original_hash is not None

    # Directly set values, bypassing Directory.update() — observer must fire.
    conference.values = {'name': 'Board Room'}
    session.flush()

    assert conference.content_hash is not None
    assert conference.content_hash != original_hash


def test_observer_fires_on_direct_file_append(session: Session) -> None:
    # Observer must fire when a file is appended directly to entry.files,
    # without going through Directory.update().
    press_releases = DirectoryCollection(session).add(
        title='Press Releases',
        structure='Title *= ___',
        configuration=DirectoryConfiguration(title='Title', order=['Title']),
    )

    entry = press_releases.add(values=dict(title='Annual Report'))
    transaction.commit()
    entry = session.query(DirectoryEntry).one()

    hash_before = entry.content_hash
    assert hash_before is not None

    new_file = DirectoryFile(
        id=random_token(),
        name='report.txt',
        note='file',
        reference=as_fileintent(
            content=BytesIO(b'test content'), filename='report.txt'
        ),
    )
    entry.files.append(new_file)
    session.flush()

    assert entry.content_hash is not None
    assert entry.content_hash != hash_before


def test_observer_fires_on_direct_file_content_change(
    session: Session,
) -> None:
    # Replacing a file (delete + append) must update the hash via the observer,
    # without going through Directory.update().
    press_releases = DirectoryCollection(session).add(
        title='Press Releases',
        structure='Title *= ___',
        configuration=DirectoryConfiguration(title='Title', order=['Title']),
    )

    entry = press_releases.add(values=dict(title='Annual Report'))
    original_file = DirectoryFile(
        id=random_token(),
        name='v1.txt',
        note='file',
        reference=as_fileintent(
            content=BytesIO(b'version 1'), filename='v1.txt'
        ),
    )
    entry.files.append(original_file)
    transaction.commit()
    entry = session.query(DirectoryEntry).one()

    hash_with_v1 = entry.content_hash
    assert hash_with_v1 is not None

    # Replace: delete the old file, append one with different content.
    old_file = entry.files[0]
    session.delete(old_file)
    replacement = DirectoryFile(
        id=random_token(),
        name='v2.txt',
        note='file',
        reference=as_fileintent(
            content=BytesIO(b'version 2'), filename='v2.txt'
        ),
    )
    entry.files.append(replacement)
    session.flush()

    assert entry.content_hash is not None
    assert entry.content_hash != hash_with_v1


# --- Known gap: in-place mutation bypasses the observer ---


def test_inplace_values_mutation_does_not_update_hash(
    session: Session,
) -> None:
    # Mutating the dict returned by entry.values in-place bypasses MutableDict
    # and the observer — the hash goes stale. The setter must be used instead.
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    original_hash = conference.content_hash
    assert original_hash is not None

    # Wrong: in-place mutation of the inner dict — observer does not fire.
    conference.values['name'] = 'Board Room'
    session.flush()
    assert conference.content_hash == original_hash  # hash is stale

    # Correct: assign through the setter — observer fires and hash updates.
    conference.values = {**conference.values, 'name': 'Board Room'}
    session.flush()
    assert conference.content_hash != original_hash


# --- Structure migration ---


def test_content_hash_changes_on_new_field(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    original_hash = conference.content_hash
    assert original_hash is not None

    # adding a new optional field migrates all entries — hash must change
    # because the values dict gains a new key
    rooms.structure = """
        Name *= ___
        Capacity = 0..999
    """
    session.flush()

    assert conference.content_hash != original_hash


# --- Upgrade (backfill for entries without a hash) ---


def test_upgrade_preserves_modified_timestamp(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='Name', order=['Name']),
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    original_modified = datetime(2020, 1, 1, tzinfo=timezone.utc)

    # simulate pre-upgrade state: no hash, known modified timestamp
    none_hash: str | None = None
    conference.content_hash = none_hash
    conference.modified = original_modified
    session.flush()

    context = Bunch(session=session, has_column=lambda table, col: True)
    calc_content_hash_for_directory_entries(cast(UpgradeContext, context))
    session.flush()

    assert conference.content_hash is not None
    assert conference.modified == original_modified
