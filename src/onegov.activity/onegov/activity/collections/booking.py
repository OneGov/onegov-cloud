from onegov.activity.models import Booking


class BookingCollection(object):

    def __init__(self, session):
        self.session = session

    def query(self):
        return self.session.query(Booking)

    def by_id(self, id):
        return self.query().filter(Booking.id == id).first()

    def by_user(self, user):
        return self.query().filter(Booking.username == user.username)

    def by_username(self, username):
        return self.query().filter(Booking.username == username)

    def add(self, user, priority=None, group_code=None,
            last_name=None, first_name=None):

        booking = Booking(
            username=user.username,
            priority=priority,
            group_code=group_code,
            last_name=last_name,
            first_name=first_name
        )

        self.session.add(booking)
        self.session.flush()

        return booking

    def delete(self, booking):
        self.session.delete(booking)
        self.sesison.flush()
