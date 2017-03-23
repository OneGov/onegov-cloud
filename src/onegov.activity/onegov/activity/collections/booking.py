from onegov.activity.models import Booking, Period
from onegov.core.collection import GenericCollection
from onegov.activity.matching.utils import unblockable, booking_order
from onegov.activity.errors import BookingLimitReached
from sqlalchemy.orm import joinedload


class BookingCollection(GenericCollection):

    def __init__(self, session, period_id=None, username=None):
        super().__init__(session)
        self.period_id = period_id
        self.username = username

    def query(self):
        query = super().query()

        if self.username is not None:
            query = query.filter(Booking.username == self.username)

        if self.period_id is not None:
            query = query.filter(Booking.period_id == self.period_id)

        return query

    def for_period(self, period):
        return self.__class__(self.session, period.id, self.username)

    def for_username(self, username):
        return self.__class__(self.session, self.period_id, username)

    @property
    def model_class(self):
        return Booking

    def count(self, usernames='*', periods='*', states='*'):
        """ Returns the number of bookings, optionally filtered by usernames,
        periods and states.

        All parameters may either be iterables or subqueries.

        """

        query = self.query().with_entities(Booking.id)

        if states != '*':
            query = query.filter(Booking.state.in_(states))

        if periods != '*':
            query = query.filter(Booking.period_id.in_(periods))

        if usernames != '*':
            query = query.filter(Booking.username.in_(usernames))

        return query.count()

    def booking_count(self, username, states='*'):
        """ Returns the number of bookings in the active period. """

        periods = self.session.query(Period)
        periods = periods.with_entities(Period.id)
        periods = periods.filter(Period.active == True)

        return self.count(
            usernames=(username, ),
            periods=periods.subquery(),
            states=states
        )

    def by_user(self, user):
        return self.query().filter(Booking.username == user.username)

    def by_username(self, username):
        return self.query().filter(Booking.username == username)

    def by_occasion(self, occasion):
        return self.query().filter(Booking.occasion_id == occasion.id)

    def add(self, user, attendee, occasion, priority=None, group_code=None):

        return super().add(
            username=user.username,
            attendee_id=attendee.id,
            occasion_id=occasion.id,
            priority=priority,
            group_code=group_code,
            period_id=occasion.period_id
        )

    def accept_booking(self, booking):
        """ Accepts the given booking, setting all other bookings which
        conflict with it to 'blocked'.

        Can only be done if the period has been confirmed already, the
        occasion is not yet full and the given booking doesn't conflict
        with another accepted booking.

        """

        if not booking.period.confirmed:
            raise RuntimeError("The period has not yet been confirmed")

        if booking.occasion.full:
            raise RuntimeError("The occasion is already full")

        if booking.state not in ('open', 'denied'):
            raise RuntimeError("Only open/denied bookings can be accepted")

        bookings = tuple(
            self.session.query(Booking)
                .options(joinedload(Booking.occasion))
                .filter(Booking.attendee_id == booking.attendee_id)
                .filter(Booking.period_id == booking.period_id)
                .filter(Booking.id != booking.id)
        )

        limit = booking.attendee.limit or booking.period.booking_limit

        if limit:
            accepted = sum(1 for b in bookings if b.state == 'accepted')

            if accepted >= limit:
                raise BookingLimitReached()

            # accepting one more booking will reach the limit
            block_rest = (accepted + 1) >= limit
        else:
            block_rest = False

        # block the overlapping bookings
        for b in bookings:
            if b.overlaps(booking):
                if b.state == 'cancelled':
                    continue

                if b.state == 'accepted':
                    raise RuntimeError("Conflict with booking {}".format(b.id))

                b.state = 'blocked'

        # if we reached the limit, block *all* bookings
        if block_rest:
            for b in bookings:
                if b.state in ('cancelled', 'accepted'):
                    continue

                b.state = 'blocked'

        booking.state = 'accepted'
        booking.cost = booking.provisional_booking_cost()

    def cancel_booking(self, booking,
                       score_function=booking_order, cascade=True):
        """ Cancels the given booking.

        If ``cascade`` is set to False, this amounts to a simple state change
        and you can stop reading now.

        If ``cascade`` is set to true, all denied bookings which have a chance
        of becoming accepted as a result (because the occasion frees up) are
        accepted according to their matching score (already accepted bookings
        are not touched).

        All bookings which get unblocked for the current user are tried
        to be accepted as well, also with the highest score first. Contrary
        to the other influenced bookings, these bookings are not limited to
        the occasion of the cancelled booking.

        This won't necesserily create a new stable matching, but it will
        keep the operability as high as possible. It's not ideal from a
        usability perspective as a single cancel may have a bigger impact
        than the user intended, but it beats having occasions fail with
        too few attendees when there are bookings waiting.

        Can only be done if the period has been confirmed already and the
        booking is an accepted bookings. Open, cancelled, blocked and
        denied bookings can simply be deleted.

        """

        if not booking.period.confirmed:
            raise RuntimeError("The period has not yet been confirmed")

        # if the booking wasn't accepted or if we don't cascade, this is quick
        if not cascade or booking.state != 'accepted':
            booking.state = 'cancelled'
            return

        bookings = tuple(
            self.session.query(Booking)
                .options(joinedload(Booking.occasion))
                .filter(Booking.attendee_id == booking.attendee_id)
                .filter(Booking.period_id == booking.period_id)
                .filter(Booking.id != booking.id))

        booking.state = 'cancelled'

        # mark the no-longer blocked bookings as denied
        accepted = {b for b in bookings if b.state == 'accepted'}
        blocked = {b for b in bookings if b.state == 'blocked'}
        unblocked = set()

        if booking.period.all_inclusive:
            limit = booking.period.booking_limit
        else:
            limit = booking.attendee.limit

        unblockable_bookings = unblockable(accepted, blocked, score_function)

        for cnt, booking in enumerate(unblockable_bookings, start=1):

            if limit and limit < (cnt + len(accepted)):
                break

            booking.state = 'denied'
            unblocked.add(booking)

        self.session.flush()

        # try to accept the denied bookings in their respective occasions
        for b in unblocked:

            # the denied state changes during the loop execution
            if b.state == 'denied' and not b.occasion.full:
                self.accept_booking(b)
                self.session.flush()

        # try to accept the open/denied bookings in the current occasion
        spots = booking.occasion.available_spots
        denied_bookings = sorted(
            (
                b for b in booking.occasion.bookings
                if b.state in ('open', 'denied')
            ),
            key=score_function)

        for b in denied_bookings:
            if spots:
                try:
                    self.accept_booking(b)
                    self.session.flush()
                    spots -= 1
                except BookingLimitReached:
                    pass
