class DuplicateHandlerError(Exception):
    """ Raised when a handler with a duplicate id or shortcode exists. """


class InvalidStateChange(Exception):
    """ Raised when an invalid state change is executed (e.g. closing an open
    ticket without the intermediary 'pending' step).

    """
