class OnegovUserError(Exception):
    """ Base class for all errors raised by onegov.user. """
    def __init__(self, message):
        self.message = message


class UnknownUserError(OnegovUserError):
    """ Raised when a user was not found. """


class InvalidActivationTokenError(OnegovUserError):
    """ Raised when the given activation token doesn't match. """


class ExistingUserError(OnegovUserError):
    """ Raised when a new user already exists. """


class AlreadyActivatedError(OnegovUserError):
    """ Raised when a user was already activated. """


class InsecurePasswordError(OnegovUserError):
    """ Raised when a user's password is not secure enough. """

    def __init__(self):
        pass
