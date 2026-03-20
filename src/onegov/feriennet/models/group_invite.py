from __future__ import annotations

from functools import cached_property
from onegov.activity.models import Attendee, Booking, Occasion, BookingPeriod
from onegov.activity.utils import random_group_code
from onegov.user import User
from sqlalchemy import func, or_
from sqlalchemy.orm import contains_eager, joinedload


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Query, Session
    from typing import Self


class GroupInvite:

    def __init__(
        self,
        session: Session,
        group_code: str,
        username: str | None
    ) -> None:
        self.session = session
        self.group_code = group_code
        self.username = username

    @classmethod
    def create(cls, session: Session, username: str | None) -> Self:
        """ Creates a new group invite with a code that is not yet used. """
        candidate = cls(
            session=session, group_code=random_group_code(), username=username)

        # this might happen once in 26⁹ tries 🤞
        if candidate.exists:
            return cls.create(session, username)

        return candidate

    def for_username(self, username: str | None) -> Self:
        return self.__class__(self.session, self.group_code, username)

    @cached_property
    def user(self) -> User | None:
        if not self.username:
            return None

        return (
            self.session.query(User)
            .filter_by(username=self.username).first()
        )

    @property
    def exists(self) -> bool:
        """ Returns True if the group_code associated with this invite exists.

        """
        return self.session.query(self.bookings().exists()).scalar()

    def bookings(self) -> Query[Booking]:
        """ Returns a query of the bookings associated with this invite. """

        return (
            self.session.query(Booking)
            .filter(Booking.group_code == self.group_code)
            .join(Booking.period)
            .filter(or_(
                Booking.state.in_(('open', 'accepted')),
                BookingPeriod.confirmed == False
            ))
            .join(Booking.attendee)
            .options(contains_eager(Booking.attendee))
            .options(contains_eager(Booking.period))
            .options(joinedload(Booking.occasion).selectinload(Occasion.dates))
        )

    @cached_property
    def occasion(self) -> Occasion:
        """ Looks up the occasion linked to this group invite.

        Technically it would be possible that a group code points to multiple
        occasions, but that would be an error. If that happens, an exception
        will be thrown.

        """

        return self.session.query(Occasion).filter(Occasion.id.in_(
            self.bookings()
            .with_entities(Booking.occasion_id)
            .scalar_subquery()
        )).one()

    @cached_property
    def attendees(self) -> tuple[tuple[Attendee, Booking], ...]:
        """ Returns the attendees linked to this invite. """
        return tuple(
            (booking.attendee, booking)
            for booking in self.bookings().order_by(
                func.unaccent(Attendee.name)
            )
        )

    def prospects(
        self,
        username: str
    ) -> Iterator[tuple[Attendee, Booking | None]]:
        """ Returns the attendees associated with the given users that are
        not yet part of the group.

        The result is a list of tuples with the first element being the
        attendee and the second element being the booking for the linked
        occasion, if such a booking already exists (otherwise None).

        """

        if not username:
            return

        existing = {a.id for a, b in self.attendees}

        attendees = (
            self.session.query(Attendee)
            .filter(Attendee.username == username)
            .order_by(func.unaccent(Attendee.name))
        )

        bookings_query = (
            self.session.query(Booking)
            .filter(Booking.occasion_id == self.occasion.id)
            .filter(Booking.attendee_id.in_(
                attendees.with_entities(Attendee.id).scalar_subquery()))
        )

        bookings = {b.attendee_id: b for b in bookings_query}

        for attendee in attendees:
            if attendee.id not in existing:
                yield attendee, bookings.get(attendee.id, None)
