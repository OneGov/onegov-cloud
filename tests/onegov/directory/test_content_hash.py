from __future__ import annotations

import transaction

from datetime import datetime, timezone
from io import BytesIO
from onegov.core.upgrade import UpgradeContext
from onegov.core.utils import Bunch
from onegov.directory import Directory
from onegov.directory import DirectoryCollection
from onegov.directory import DirectoryConfiguration
from onegov.directory import DirectoryEntry
from onegov.directory.upgrade import calc_content_hash_for_directory_entries
from typing import TYPE_CHECKING, cast
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_content_hash_on_create(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="Name *= ___",
        configuration=DirectoryConfiguration(title='Name', order=['Name'])
    )

    conference = rooms.add(values=dict(name='Conference Room'))

    assert conference.content_hash is not None
    assert len(conference.content_hash) == 64  # SHA-256 hex digest


def test_content_hash_changes_on_update(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="""
            Name *= ___
            Note = ___
        """,
        configuration=DirectoryConfiguration(title='Name', order=['Name'])
    )

    conference = rooms.add(values=dict(name='Conference Room', note='Nice'))
    original_hash = conference.content_hash
    assert original_hash is not None

    rooms.update(conference, dict(name='Conference Room', note='Even nicer'))

    assert conference.content_hash != original_hash


def test_content_hash_stable_when_no_change(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="Name *= ___",
        configuration=DirectoryConfiguration(title='Name', order=['Name'])
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
        configuration=DirectoryConfiguration(title='Title', order=['Title'])
    )

    txt = Bunch(
        data=object(),
        file=BytesIO(b'original content'),
        filename='report.txt'
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
    press_releases.update(entry, dict(
        title='Annual Report',
        file=Bunch(data={}, action='delete')
    ))
    commit()

    assert entry.content_hash != hash_with_file

    # add a new file — hash must change again
    txt2 = Bunch(
        data=object(),
        file=BytesIO(b'updated content'),
        filename='report-v2.txt'
    )
    press_releases.update(entry, dict(title='Annual Report', file=txt2))
    commit()

    assert entry.content_hash != hash_with_file


def test_content_hash_set_by_before_flush_listener(session: Session) -> None:
    # Verifies the before_flush listener fires as a safety net when an entry
    # has no hash at flush time (e.g. a future mutation path bypasses
    # Directory.update(), or the hash is explicitly cleared).
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="Name *= ___",
        configuration=DirectoryConfiguration(title='Name', order=['Name'])
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    assert conference.content_hash is not None

    # Simulate a missing hash (e.g. after a partial migration or a direct
    # attribute assignment that bypassed update_content_hash).
    none_hash: str | None = None
    conference.content_hash = none_hash
    session.flush()

    assert conference.content_hash is not None
    assert len(conference.content_hash) == 64


def test_upgrade_preserves_modified_timestamp(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="Name *= ___",
        configuration=DirectoryConfiguration(title='Name', order=['Name'])
    )

    conference = rooms.add(values=dict(name='Conference Room'))
    original_modified = datetime(2020, 1, 1, tzinfo=timezone.utc)

    # simulate pre-upgrade state: no hash, known modified timestamp
    none_hash: str | None = None
    conference.content_hash = none_hash
    conference.modified = original_modified
    session.flush()

    context = Bunch(
        session=session,
        has_column=lambda table, col: True
    )
    calc_content_hash_for_directory_entries(cast(UpgradeContext, context))
    session.flush()

    assert conference.content_hash is not None
    assert conference.modified == original_modified


def test_content_hash_changes_on_new_field(session: Session) -> None:
    rooms = DirectoryCollection(session).add(
        title='Rooms',
        structure="Name *= ___",
        configuration=DirectoryConfiguration(title='Name', order=['Name'])
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
