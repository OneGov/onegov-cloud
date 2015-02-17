class OnegovServerError(Exception):
    def __init__(self, message):
        self.message = message


class ApplicationConflictError(OnegovServerError):
    pass
