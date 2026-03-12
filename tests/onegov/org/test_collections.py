from __future__ import annotations

import pytest

from datetime import timedelta
from onegov.directory import DirectoryCollection, DirectoryConfiguration
from onegov.org.models.directory import ExtendedDirectoryEntryCollection
from pytz import UTC
from sedate import utcnow, to_timezone
from sqlalchemy import text


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.org.models.directory import ExtendedDirectory
    from sqlalchemy.orm import Session


@pytest.mark.parametrize('start_offset,end_offset,is_published', [
    (None, timedelta(minutes=1), True),
    (timedelta(minutes=20), None, False),
    (timedelta(minutes=-40), None, True),
    (None, None, True),
    (None, timedelta(minutes=-40), False),
])
def test_extended_directory_entry_collection(
    session: Session,
    start_offset: timedelta | None,
    end_offset: timedelta | None,
    is_published: bool
) -> None:
    """
    Test hybrid_properties and postgres setup at the same time
    """

    utc_now = utcnow()
    now = to_timezone(utc_now, 'Europe/Zurich')
    start = now + start_offset if start_offset else None
    end = now + end_offset if end_offset else None

    directories: DirectoryCollection[ExtendedDirectory]
    directories = DirectoryCollection(session, type='extended')
    directory = directories.add(
        title="Sample",
        structure="Name *= ___",
        configuration=DirectoryConfiguration(
            title="[name]",
            order=['name']
        )
    )
    session.add(directory)
    session.flush()

    entry = directory.add(dict(
        name='Sample Entry',
        directory_id=directory.id,
        order='name',
        publication_start=start,
        publication_end=end,
    ))

    collection = ExtendedDirectoryEntryCollection(directory)

    assert collection.query().count() == 1
    collection.published_only = True
    if end_offset:
        assert entry.publication_end is not None
        # why on earth are CET values returned?
        assert entry.publication_end.tzinfo == UTC

    if is_published:
        # test hybrid properties on instances
        assert not entry.publication_ended
        assert entry.publication_started
    assert entry.published == is_published

    # Test the hybrid_property expressions on class per query
    session.execute(text("SET TIME ZONE 'GMT';"))
    assert collection.query().count() == (1 if is_published else 0)
