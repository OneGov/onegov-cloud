class NewsletterException(Exception):
    pass


class AlreadyExistsError(NewsletterException):
    """ Raised if a newsletter exists already. """
