from __future__ import annotations


class OnegovUserError(Exception):
    """ Base class for all errors raised by onegov.user. """
    def __init__(self, message: str):
        self.message = message


class UnknownUserError(OnegovUserError):
    """ Raised when a user was not found. """


class InvalidActivationTokenError(OnegovUserError):
    """ Raised when the given activation token doesn't match. """


class ExistingUserError(OnegovUserError):
    """ Raised when a new user already exists. """


class AlreadyActivatedError(OnegovUserError):
    """ Raised when a user was already activated. """


class ExpiredSignupLinkError(OnegovUserError):
    """ Raised when the signup link in use has expired. """

    def __init__(self) -> None:
        pass


class InsecurePasswordError(OnegovUserError):
    """ Raised when a user's password is not secure enough. """

    def __init__(self) -> None:
        pass


class RateLimitError(OnegovUserError):
    """ Raised when the IP-based login rate limit is exceeded. """

    def __init__(self) -> None:
        pass


class AccountLockedError(OnegovUserError):
    """ Raised when an account is temporarily locked due to too many
    failed login attempts. """

    def __init__(self, minutes_remaining: int) -> None:
        self.minutes_remaining = minutes_remaining
