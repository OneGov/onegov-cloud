class CSVError(Exception):
    pass


class MissingColumnsError(CSVError):
    def __init__(self, columns):
        self.columns = columns


class AmbiguousColumnsError(CSVError):
    def __init__(self, columns):
        self.columns = columns


class DuplicateColumnNames(CSVError):
    pass


class InvalidFormat(CSVError):
    pass


class EmptyFile(CSVError):
    pass
