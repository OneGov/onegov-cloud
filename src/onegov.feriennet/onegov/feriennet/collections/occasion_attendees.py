from collections import namedtuple, OrderedDict
from onegov.activity import Activity, Attendee, Occasion, OccasionCollection
from onegov.user import User


OccasionAttendee = namedtuple('OccasionAttendee', ('attendee', 'contact'))


class OccasionAttendeeCollection(OccasionCollection):

    def __init__(self, session, period, username=None):
        super().__init__(session)
        self.period = period
        self.username = username

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period, self.username)

    def query(self):
        q = super().query()
        q = q.join(Occasion.activity)

        # this will implicitly filter out all occasions without attendees:
        q = q.join(Occasion.accepted)

        q = q.filter(Occasion.period_id == self.period_id)

        if self.username:
            q = q.filter(Activity.username == self.username)

        return q.order_by(Activity.title, Occasion.start, Occasion.id)

    def occasions(self):
        occasions = OrderedDict()

        attendees = {
            attendee.id: attendee for attendee in self.session.query(Attendee)
        }

        contacts = {
            u.username: u.data and u.data.get('emergency')
            for u in self.session.query(
                User.username, User.data
            )
        }

        for o in self.query():
            occasions[o] = [
                OccasionAttendee(
                    attendees[b.attendee_id],
                    contacts[b.username]
                ) for b in sorted(
                    o.accepted,
                    key=lambda b: attendees[b.attendee_id].name
                )
            ]

        return occasions
