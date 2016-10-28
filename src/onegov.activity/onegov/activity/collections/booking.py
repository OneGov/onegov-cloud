from onegov.activity.models import Booking
from onegov.core.collection import GenericCollection


class BookingCollection(GenericCollection):

    @property
    def model_class(self):
        return Booking

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
