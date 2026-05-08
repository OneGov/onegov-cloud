from __future__ import annotations

from abc import abstractmethod


from typing import Protocol, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from _typeshed import SupportsRichComparison
    from collections.abc import Sequence
    from datetime import datetime
    from decimal import Decimal
    from onegov.activity.models.booking import BookingState


class MatchableOccasionDate(Protocol):
    """ Describes the interface required by the occasion date class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """
    @property
    def start(self) -> datetime:
        """ The start of the occasion. """

    @property
    def end(self) -> datetime:
        """ The end of the occasion. """


# FIXME: We should replace this by typing.Protocol and add some of the
#        new attributes the algorithm relies on, since this minimal
#        interface is no longer quite sufficient.
class MatchableOccasion(Protocol):
    """ Describes the interface required by the occasion class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    @property
    @abstractmethod
    def id(self) -> SupportsRichComparison:
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
    def dates(self) -> Sequence[MatchableOccasionDate]:
        """ Returns the dates of the occasion. """

    @property
    @abstractmethod
    def anti_affinity_group(self) -> str:
        """ Forces the occasion to not be accept an attendee that has an
        occasion of the same anti-affinity-group.

        Note that the anti-affinity-group is ignored if the occasion
        is excluded from overlap checks.

        See :meth:`exclude_from_overlap_check`.

        """


class MatchableBooking(Protocol):
    """ Describes the interface required by the booking class used by
    the algorithm.

    This allows us to untie our implementation from the database.

    """

    score: Decimal
    occasion: MatchableOccasion

    @abstractmethod
    def __eq__(self, other: object) -> bool:
        """ The class must be comparable to other classes. """

    @abstractmethod
    def __hash__(self) -> int:
        """ The class must be hashable. """

    @property
    @abstractmethod
    def id(self) -> SupportsRichComparison:
        """ The id of the booking. """

    @property
    @abstractmethod
    def occasion_id(self) -> SupportsRichComparison:
        """ Returns the id of the occasion this booking belongs to. """

    @property
    @abstractmethod
    def attendee_id(self) -> SupportsRichComparison:
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

    @property
    @abstractmethod
    def dates(self) -> Sequence[MatchableOccasionDate]:
        """ Returns the dates of the booking. """

    @property
    @abstractmethod
    def group_code(self) -> str | None:
        """ A code holding groups together. Grouped bookings are preferred
        over other bookings (so that groups may stay together).

        """

    @abstractmethod
    def overlaps(
        self,
        other: Self,
        with_anti_affinity_check: bool = False
    ) -> bool:
        """ Returns whether or not this overlaps the other booking. """
