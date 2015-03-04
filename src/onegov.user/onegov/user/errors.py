class OnegovUserError(Exception):
    """ Base class for all errors raised by onegov.user. """
    def __init__(self, message):
        self.message = message


class UnknownUserError(OnegovUserError):
    """ Raised when a user was not found. """
