class OnegovDirectoryError(Exception):
    pass


class ValidationError(OnegovDirectoryError):
    def __init__(self, errors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.errors = errors
