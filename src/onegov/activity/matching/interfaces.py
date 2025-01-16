from __future__ import annotations

from abc import ABCMeta, abstractmethod


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from onegov.activity.models import OccasionDate
    from onegov.activity.models.booking import BookingState
    from uuid import UUID


class MatchableOccasion(metaclass=ABCMeta):
    """ Describes the interface required by the occasion class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    @property
    @abstractmethod
    def id(self) -> UUID:
        """ The id of the occasion. """

    @property
    @abstractmethod
    def max_spots(self) -> int:
        """ The maximum number of available spots. """

    @property
    @abstractmethod
    def exclude_from_overlap_check(self) -> bool:
        """ True if bookings of this occasion are ignored during overlap
        checks.

        """

    @property
    @abstractmethod
    def anti_affinity_group(self) -> str:
        """ Forces the occasion to not be accept an attendee that has an
        occasion of the same anti-affinity-group.

        Note that the anti-affinity-group is ignored if the occasion
        is excluded from overlap checks.

        See :meth:`exclude_from_overlap_check`.

        """


class MatchableBooking(metaclass=ABCMeta):
    """ Describes the interface required by the booking class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """ The class must be comparable to other classes. """

    @abstractmethod
    def __hash__(self) -> int:
        """ The class must be hashable. """

    @property
    @abstractmethod
    def id(self) -> UUID:
        """ The id of the booking. """

    @property
    @abstractmethod
    def occasion_id(self) -> UUID:
        """ Returns the id of the occasion this booking belongs to. """

    @property
    @abstractmethod
    def attendee_id(self) -> UUID:
        """ Returns the id of the attendee this booking belongs to. """

    @property
    @abstractmethod
    def state(self) -> BookingState:
        """ Returns the state of the booking, one of:

        * "open" (for unassigned bookings)
        * "accepted" (for already accepted bookings)
        * "blocked" (for bookings blocked by another accepted booking)

        """

    @property
    @abstractmethod
    def priority(self) -> int:
        """ Returns the priority of the booking. The higher the priority
        the further up the wishlist.

        Bookings further up the wishlist are first passed to the occasions.
        All things being equal (i.e. the scores of the other bookings), this
        leads to a higher chance of placement.

        """

    # FIXME: We probably also need to define an interface for OccasionDate
    @property
    @abstractmethod
    def dates(self) -> Sequence[OccasionDate]:
        """ Returns the dates of the booking. """

    @property
    @abstractmethod
    def group_code(self) -> str | None:
        """ A code holding groups together. Grouped bookings are preferred
        over other bookings (so that groups may stay together).

        """
