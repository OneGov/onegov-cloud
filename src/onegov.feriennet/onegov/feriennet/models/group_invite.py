from cached_property import cached_property
from onegov.activity.models import Attendee, Booking, Occasion, Period
from onegov.activity.utils import random_group_code
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload


class GroupInvite(object):

    def __init__(self, session, group_code):
        self.session = session
        self.group_code = group_code

    @classmethod
    def create(cls, session):
        """ Creates a new group invite with a code that is not yet used. """
        candidate = cls(session, group_code=random_group_code())

        # this might happen once in 26⁹ tries 🤞
        if candidate.exists:
            return cls.create(session)

        return candidate

    @property
    def exists(self):
        """ Returns True if the group_code associated with this invite exists.

        """
        return self.session.query(self.bookings().exists()).scalar()

    def bookings(self):
        """ Returns a query of the bookings associated with this invite. """

        return self.session.query(Booking)\
            .options(joinedload(Booking.attendee))\
            .options(joinedload(Booking.occasion))\
            .options(joinedload(Booking.period))\
            .filter_by(group_code=self.group_code)\
            .filter(or_(
                Booking.state.in_(('open', 'accepted')),
                Period.confirmed == False
            ))

    @cached_property
    def occasion(self):
        """ Looks up the occasion linked to this group invite.

        Technically it would be possible that a group code points to multiple
        occasions, but that would be an error. If that happens, an exception
        will be thrown.

        """

        return self.session.query(Occasion).filter(Occasion.id.in_(
            self.bookings().with_entities(Booking.occasion_id).subquery()
        )).one()

    @cached_property
    def attendees(self):
        """ Returns the attendees linked to this invite. """

        return tuple(
            (booking.attendee, booking) for booking in self.bookings()
            .outerjoin(Attendee)
            .order_by(func.unaccent(Attendee.name))
        )

    def prospects(self, username):
        """ Returns the attendees associated with the given users that are
        not yet part of the group.

        The result is a list of tuples with the first element being the
        attendee and the second element being the booking for the linked
        occasion, if such a booking already exists (otherwise None).

        """

        if not username:
            return

        existing = {a.id for a, b in self.attendees}

        attendees = self.session.query(Attendee)\
            .filter(Attendee.username == username)\
            .order_by(func.unaccent(Attendee.name))

        bookings = self.session.query(Booking)\
            .filter(Booking.occasion_id == self.occasion.id)\
            .filter(Booking.attendee_id.in_(
                attendees.with_entities(Attendee.id).subquery()))

        bookings = {b.attendee_id: b for b in bookings}

        for attendee in attendees:
            if attendee.id not in existing:
                yield attendee, bookings.get(attendee.id, None)
