from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class CSVError(Exception):
    pass


class MissingColumnsError(CSVError):
    def __init__(self, columns: Sequence[str]):
        self.columns = columns


class AmbiguousColumnsError(CSVError):
    def __init__(self, columns: Mapping[str, Sequence[str]]):
        self.columns = columns


class DuplicateColumnNamesError(CSVError):
    pass


class InvalidFormatError(CSVError):
    pass


class EmptyFileError(CSVError):
    pass


class EmptyLineInFileError(CSVError):
    pass


class AlreadyLockedError(Exception):
    """ Raised if :func:`onegov.core.utils.lock` fails to acquire a lock. """
