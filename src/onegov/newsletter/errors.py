from __future__ import annotations


class NewsletterException(Exception):
    pass


class AlreadyExistsError(NewsletterException):
    """ Raised if a newsletter exists already. """
