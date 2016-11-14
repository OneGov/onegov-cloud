import sedate

from onegov.activity import log


def overlaps(booking, other):
    """ Returns true if the two given bookings overlap. """

    assert booking != other

    return sedate.overlaps(
        booking.start, booking.end,
        other.start, other.end
    )


class LoopBudget(object):
    """ Helps ensure that a loop doesn't overreach its complexity budget.

    For example::

        budget = LoopBudget(max_ticks=10)

        while True:
            if budget.limit_reached():
                break
    """

    def __init__(self, max_ticks):
        self.ticks = 0
        self.max_ticks = max_ticks

    def limit_reached(self, as_exception=False):
        self.ticks += 1

        if self.ticks >= self.max_ticks:
            message = "Loop limit of {} has been reached".format(self.ticks)

            if as_exception:
                raise RuntimeError(message)
            else:
                log.warning(message)

            return True


def hashable(attribute):

    class Hashable(object):

        def __hash__(self):
            return hash(getattr(self, attribute))

        def __eq__(self, other):
            return getattr(self, attribute) == getattr(other, attribute)

    return Hashable
