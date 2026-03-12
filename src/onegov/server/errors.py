from __future__ import annotations


class OnegovServerError(Exception):
    """ Base class for all errors raised by onegov.server. """
    def __init__(self, message: str):
        self.message = message


class ApplicationConflictError(OnegovServerError):
    """ Raised if an application conflicts with another application. """


class ApplicationConfigError(OnegovServerError):
    """ Raised when there's an error in an application configuration. """
