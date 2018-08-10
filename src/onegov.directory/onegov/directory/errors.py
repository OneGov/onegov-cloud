class OnegovDirectoryError(Exception):
    pass


class ValidationError(OnegovDirectoryError):
    def __init__(self, entry, errors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entry = entry
        self.errors = errors


class MissingColumnError(OnegovDirectoryError):
    def __init__(self, column, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.column = column


class DuplicateEntryError(OnegovDirectoryError):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name


class MissingFileError(OnegovDirectoryError):
    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = name
