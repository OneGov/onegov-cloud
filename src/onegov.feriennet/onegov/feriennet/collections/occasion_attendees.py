from collections import namedtuple, OrderedDict, Counter
from onegov.activity import Activity, Attendee, Occasion, OccasionCollection
from onegov.user import User


OccasionAttendee = namedtuple(
    'OccasionAttendee', ('attendee', 'info', 'group_code'))


class OccasionAttendeeCollection(OccasionCollection):

    def __init__(self, session, period, activity, username=None):
        super().__init__(session)
        self.period = period
        self.username = username
        self.activity = activity

    @property
    def period_id(self):
        return self.period.id

    @property
    def activity_name(self):
        return self.activity.name

    def for_period(self, period):
        return self.__class__(
            self.session, period, self.activity, self.username)

    def query(self):
        q = super().query()
        q = q.join(Occasion.activity)

        # this will implicitly filter out all occasions without attendees:
        q = q.join(Occasion.accepted)

        q = q.filter(Occasion.period_id == self.period_id)
        q = q.filter(Occasion.activity_id == self.activity.id)

        if self.username:
            q = q.filter(Activity.username == self.username)

        return q.order_by(Activity.title, Occasion.order, Occasion.id)

    def occasions(self):
        occasions = OrderedDict()

        attendees = {
            attendee.id: attendee for attendee in self.session.query(Attendee)
        }

        contacts = {
            u.username: {
                'emergency': u.data and u.data.get('emergency'),
                'email': u.data and u.data.get('email') or u.username,
                'place': u.data and u.data.get('place'),
            }
            for u in self.session.query(
                User.username, User.data
            )
        }

        for o in self.query():
            group_codes = Counter(b.group_code for b in o.accepted)

            occasions[o] = [
                OccasionAttendee(
                    attendee=attendees[b.attendee_id],
                    info=contacts[b.username],
                    group_code=(
                        group_codes[b.group_code] > 1 and b.group_code or None
                    )
                ) for b in sorted(
                    o.accepted,
                    key=lambda b: attendees[b.attendee_id].name
                )
            ]

        return occasions
