class OnegovUserError(Exception):
    def __init__(self, message):
        self.message = message


class UnknownUserError(OnegovUserError):
    pass
