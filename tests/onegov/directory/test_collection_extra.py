from __future__ import annotations

from onegov.directory import DirectoryCollection
from onegov.directory.collections.directory import EntryRecipientCollection
from onegov.directory.types import DirectoryConfiguration


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _add(directories: DirectoryCollection[Any], title: str) -> Any:
    return directories.add(
        title=title,
        lead='Lead',
        structure='Name *= ___',
        configuration=DirectoryConfiguration(title='[Name]', order=['Name']),
    )


def test_directory_collection_add_and_unique_name(session: Session) -> None:
    directories = DirectoryCollection(session, type='generic')

    first = _add(directories, 'My Directory')
    assert first.name == 'my-directory'
    assert first.title == 'My Directory'

    # a second directory with the same title gets an incremented name
    second = _add(directories, 'My Directory')
    assert second.name == 'my-directory-1'

    assert directories.by_name('my-directory') is first
    assert directories.by_name('missing') is None


def test_directory_collection_from_yaml_configuration(
    session: Session
) -> None:
    directories = DirectoryCollection(session, type='generic')
    configuration = 'title: "[Name]"\norder:\n  - Name\n'
    directory = directories.add(
        title='Yaml Directory',
        lead='Lead',
        structure='Name *= ___',
        configuration=configuration,
    )
    assert directory.configuration.title == '[Name]'


def test_entry_recipient_collection(session: Session) -> None:
    directories = DirectoryCollection(session, type='generic')
    directory = _add(directories, 'Dir')

    recipients = EntryRecipientCollection(session)
    recipient = recipients.add(
        address='user@example.org', directory_id=directory.id)

    assert recipients.by_address('user@example.org') is recipient
    assert recipients.by_id(recipient.id) is recipient
    # a non-uuid value returns None instead of raising
    assert recipients.by_id('not-a-uuid') is None  # type: ignore[arg-type]
    assert recipients.by_inactive().count() == 0

    recipients.delete(recipient)
    assert recipients.query().count() == 0
