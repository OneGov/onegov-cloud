from onegov.activity.models import Booking, Period
from onegov.core.collection import GenericCollection


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

    def wishlist_count(self, username):
        """ Returns the number wishlist entries in the active period.

        This value is equal to the number of bookings for a given user in
        the active period.

        """

        periods = self.session.query(Period)
        periods = periods.with_entities(Period.id)
        periods = periods.filter(Period.active == True)
        periods = periods.filter(Period.confirmed == False)

        return self.count(
            usernames=(username, ),
            periods=periods.subquery(),
            states='*'
        )

    def booking_count(self, username):
        """ Returns the number of accepted bookings in the active period. """

        periods = self.session.query(Period)
        periods = periods.with_entities(Period.id)
        periods = periods.filter(Period.active == True)
        periods = periods.filter(Period.confirmed == True)

        return self.count(
            usernames=(username, ),
            periods=periods.subquery(),
            states=('accepted', )
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
