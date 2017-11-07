class OnegovDirectoryError(Exception):
    pass


class ValidationError(OnegovDirectoryError):
    def __init__(self, entry, errors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.entry = entry
        self.errors = errors
