class CSVError(Exception):
    pass


class MissingColumnsError(CSVError):
    def __init__(self, columns):
        self.columns = columns


class AmbiguousColumnsError(CSVError):
    def __init__(self, columns):
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
