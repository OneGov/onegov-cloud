from abc import ABCMeta, abstractmethod


class MatchableOccasion(metaclass=ABCMeta):
    """ Describes the interface required by the occasion class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    @property
    @abstractmethod
    def id(self):
        """ The id of the occasion. """

    @property
    @abstractmethod
    def max_spots(self):
        """ The maximum number of available spots. """

    @property
    @abstractmethod
    def exclude_from_overlap_check(self):
        """ True if bookings of this occasion are ignored during overlap
        checks.

        """


class MatchableBooking(metaclass=ABCMeta):
    """ Describes the interface required by the booking class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    def __eq__(self, other):
        """ The class must be comparable to other classes. """

    @abstractmethod
    def __hash__(self):
        """ The class must be hashable. """

    @property
    @abstractmethod
    def id(self):
        """ The id of the booking. """

    @property
    @abstractmethod
    def occasion_id(self):
        """ Returns the id of the occasion this booking belongs to. """

    @property
    @abstractmethod
    def attendee_id(self):
        """ Returns the id of the attendee this booking belongs to. """

    @property
    @abstractmethod
    def state(self):
        """ Returns the state of the booking, one of:

        * "open" (for unassigned bookings)
        * "accepted" (for already accepted bookings)
        * "blocked" (for bookings blocked by another accepted booking)

        """

    @property
    @abstractmethod
    def priority(self):
        """ Returns the priority of the booking. The higher the priority
        the further up the wishlist.

        Bookings further up the wishlist are first passed to the occasions.
        All things being equal (i.e. the scores of the other bookings), this
        leads to a higher chance of placement.

        """

    @property
    @abstractmethod
    def dates(self):
        """ Returns the dates of the booking. """
