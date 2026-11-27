from __future__ import annotations

from onegov.directory.errors import (
    DuplicateEntryError,
    MissingColumnError,
    MissingFileError,
    OnegovDirectoryError,
)


def test_missing_column_error() -> None:
    error = MissingColumnError('name')
    assert error.column == 'name'
    assert isinstance(error, OnegovDirectoryError)


def test_duplicate_entry_error() -> None:
    error = DuplicateEntryError('entry-a')
    assert error.name == 'entry-a'
    assert isinstance(error, OnegovDirectoryError)


def test_missing_file_error() -> None:
    error = MissingFileError('file.pdf')
    assert error.name == 'file.pdf'
    assert isinstance(error, OnegovDirectoryError)
