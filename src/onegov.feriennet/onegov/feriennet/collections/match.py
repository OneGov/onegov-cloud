from collections import OrderedDict
from itertools import groupby
from onegov.activity import Activity, Booking, Attendee, Occasion
from statistics import mean
from sqlalchemy import func


class MatchCollection(object):

    def __init__(self, session, period, username):
        self.session = session
        self.period = period
        self.username = username

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period, self.username)

    @property
    def base(self):
        q = self.session.query(Booking)
        q = q.with_entities(
            Booking.state.label('booking_state'),
            Activity.title.label('activity_title'),
            Occasion.id.label('occasion_id'),
            Occasion.start.label('occasion_start'),
            Occasion.end.label('occasion_end'),
            Occasion.timezone.label('occasion_timezone'),
            Occasion.spots.label('occasion_spots'),
            Attendee.name.label('attendee_name'),
            Attendee.age.label('attendee_age')
        )
        q = q.filter(Booking.period_id == self.period.id)

        if self.username:
            q = q.filter(Activity.username == self.username)

        q = q.order_by(Activity.name)
        q = q.order_by(Occasion.start)
        q = q.order_by(Occasion.id)
        q = q.join(Occasion)
        q = q.join(Activity)
        q = q.join(Attendee)

        return q

    @property
    def happiness(self):
        q = self.session.query(Attendee)
        q = q.with_entities(Attendee.happiness(self.period_id))

        return mean(a.happiness for a in q if a.happiness is not None)

    @property
    def operability(self):
        accepted = self.session.query(Booking)\
            .with_entities(func.count(Booking.id).label('count'))\
            .filter(Booking.occasion_id == Occasion.id)\
            .filter(Booking.period_id == self.period_id)\
            .filter(Booking.state == 'accepted')\
            .subquery().lateral()

        o = self.session.query(Occasion, accepted.c.count)

        bits = []

        for occasion, count in o:
            bits.append(count >= occasion.spots.lower and 1 or 0)

        if not bits:
            return 0

        return sum(bits) / len(bits)

    @property
    def occasions(self):
        occasions = OrderedDict()

        for oid, records in groupby(self.base, key=lambda r: r.occasion_id):
            occasions[oid] = {
                'first': None,
                'accepted': [],
                'other': [],
                'state': None
            }

            for ix, record in enumerate(records):
                if ix == 0:
                    occasions[oid]['first'] = record
                if record.booking_state == 'accepted':
                    occasions[oid]['accepted'].append(record)
                else:
                    occasions[oid]['other'].append(record)

            max_spots = occasions[oid]['first'].occasion_spots.upper - 1
            min_spots = occasions[oid]['first'].occasion_spots.lower

            if len(occasions[oid]['accepted']) == 0:
                occasions[oid]['state'] = 'empty'

            elif len(occasions[oid]['accepted']) < min_spots:
                occasions[oid]['state'] = 'unoperable'

            elif len(occasions[oid]['accepted']) < max_spots:
                occasions[oid]['state'] = 'operable'

            elif len(occasions[oid]['accepted']) >= max_spots:
                occasions[oid]['state'] = 'full'

        return occasions
