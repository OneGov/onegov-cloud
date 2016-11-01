from onegov.activity.models import Booking, Occasion
from onegov.activity.collections.occasion import OccasionCollection
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
            o = OccasionCollection(self.session).query()
            o = o.with_entities(Occasion.id)
            o = o.filter(Occasion.period_id == self.period_id)
            o = o.subquery()

            query = query.filter(Booking.occasion_id.in_(o))

        return query

    def for_period(self, period):
        return self.__class__(self.session, period.id, self.username)

    def for_username(self, username):
        return self.__class__(self.session, self.period_id, username)

    @property
    def model_class(self):
        return Booking

    def count(self, username, state='unconfirmed'):
        """ Returns the number of bookings for the given username and state.

        """

        query = self.query().with_entities(Booking.id)
        query = query.filter(Booking.state == state)
        query = query.filter(Booking.username == username)

        return query.count()

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
        )
