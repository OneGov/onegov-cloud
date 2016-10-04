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

    def add(self, user, priority=None, group_code=None,
            last_name=None, first_name=None):

        return super().add(
            username=user.username,
            priority=priority,
            group_code=group_code,
            last_name=last_name,
            first_name=first_name
        )
