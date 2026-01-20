from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.directory.models import DirectoryEntry
    from wtforms.form import _FormErrors


class OnegovDirectoryError(Exception):
    pass


class ValidationError(OnegovDirectoryError):
    def __init__(
        self,
        entry: DirectoryEntry,
        errors: _FormErrors,
        *args: object
    ) -> None:

        super().__init__(*args)
        self.entry = entry
        self.errors = errors


class MissingColumnError(OnegovDirectoryError):
    def __init__(self, column: str, *args: object) -> None:
        super().__init__(*args)
        self.column = column


class DuplicateEntryError(OnegovDirectoryError):
    def __init__(self, name: str, *args: object) -> None:
        super().__init__(*args)
        self.name = name


class MissingFileError(OnegovDirectoryError):
    def __init__(self, name: str, *args: object) -> None:
        super().__init__(*args)
        self.name = name
