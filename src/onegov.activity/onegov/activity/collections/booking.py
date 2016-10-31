from onegov.activity.models import Booking
from onegov.core.collection import GenericCollection


class BookingCollection(GenericCollection):

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
