from collections import OrderedDict
from itertools import groupby
from onegov.activity import Activity, Booking, Attendee, Occasion, OccasionDate
from statistics import mean
from sqlalchemy import func, literal_column, not_, distinct


class MatchCollection(object):

    def __init__(self, session, period, states=None):
        self.session = session
        self.period = period
        self.states = set(states) if states else set()

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period)

    def for_filter(self, state=None):

        def toggle(collection, item):
            if item is None:
                return collection

            if item in collection:
                return collection - {item}
            else:
                return collection | {item}

        toggled = (
            toggle(collection, item) for collection, item in (
                (self.states, state),
            )
        )

        return self.__class__(self.session, self.period, *toggled)

    @property
    def base(self):
        d = self.session.query(OccasionDate)
        d = d.with_entities(OccasionDate.id)
        d = d.order_by(OccasionDate.occasion_id, OccasionDate.start)
        d = d.distinct(OccasionDate.occasion_id)

        q = self.session.query(Booking)
        q = q.with_entities(
            Booking.id.label('booking_id'),
            Booking.state.label('booking_state'),
            Booking.nobbled.label('booking_nobbled'),
            Activity.title.label('activity_title'),
            Occasion.id.label('occasion_id'),
            Occasion.cancelled.label('occasion_cancelled'),
            OccasionDate.start.label('occasion_start'),
            OccasionDate.end.label('occasion_end'),
            OccasionDate.timezone.label('occasion_timezone'),
            Occasion.spots.label('occasion_spots'),
            Occasion.age.label('occasion_age'),
            Occasion.order.label('occasion_order'),
            Attendee.id.label('attendee_id'),
            Attendee.name.label('attendee_name'),
            Attendee.age.label('attendee_age'),
            Attendee.username.label('attendee_username'),
        )
        q = q.filter(Booking.period_id == self.period.id)
        q = q.filter(OccasionDate.id.in_(d.subquery()))

        q = q.join(Occasion)
        q = q.join(OccasionDate)
        q = q.join(Activity)
        q = q.join(Attendee)

        # include the occasions for which there is no booking
        e = self.session.query(Occasion)
        e = e.with_entities(
            literal_column('NULL').label('booking_id'),
            literal_column('NULL').label('booking_state'),
            literal_column('NULL').label('booking_nobbled'),
            Activity.title.label('activity_title'),
            Occasion.id.label('occasion_id'),
            Occasion.cancelled.label('occasion_cancelled'),
            OccasionDate.start.label('occasion_start'),
            OccasionDate.end.label('occasion_end'),
            OccasionDate.timezone.label('occasion_timezone'),
            Occasion.spots.label('occasion_spots'),
            Occasion.age.label('occasion_age'),
            Occasion.order.label('occasion_order'),
            literal_column('NULL').label('attendee_id'),
            literal_column('NULL').label('attendee_name'),
            literal_column('NULL').label('attendee_age'),
            literal_column('NULL').label('attendee_username'),
        )
        e = e.filter(Occasion.period_id == self.period.id)
        e = e.filter(not_(
            Occasion.id.in_(
                self.session.query(distinct(Booking.occasion_id))
                .filter(Booking.period_id == self.period.id)
                .subquery()
            )
        ))
        e = e.filter(OccasionDate.id.in_(d.subquery()))

        e = e.join(Occasion.dates)
        e = e.join(Occasion.activity)

        return q.union(e).order_by(
            'activity_title',
            'occasion_order',
            'occasion_id',
            'attendee_name',
        )

    @property
    def happiness(self):
        q = self.session.query(Attendee)
        q = q.with_entities(Attendee.happiness(self.period_id))

        values = tuple(a.happiness for a in q if a.happiness is not None)

        if values:
            return mean(values)
        else:
            return 0

    @property
    def operability(self):
        accepted = self.session.query(Booking)\
            .with_entities(func.count(Booking.id).label('count'))\
            .filter(Booking.occasion_id == Occasion.id)\
            .filter(Booking.period_id == self.period_id)\
            .filter(Booking.state == 'accepted')\
            .subquery().lateral()

        o = self.session.query(Occasion.spots, accepted.c.count)
        o = o.filter(Occasion.period_id == self.period_id)

        bits = []

        for spots, count in o:
            bits.append(count >= spots.lower and 1 or 0)

        if not bits:
            return 0

        return sum(bits) / len(bits)

    def include_in_output(self, occasion):
        if not self.states:
            return True

        return occasion['state'] in self.states

    @property
    def occasions(self):
        occasions = OrderedDict()

        for oid, records in groupby(self.base, key=lambda r: r.occasion_id):
            occasion = {
                'first': None,
                'accepted': [],
                'other': [],
                'state': None
            }

            for ix, record in enumerate(records):
                if ix == 0:
                    occasion['first'] = record
                if record.booking_state == 'accepted':
                    occasion['accepted'].append(record)
                else:
                    occasion['other'].append(record)

            max_spots = occasion['first'].occasion_spots.upper - 1
            min_spots = occasion['first'].occasion_spots.lower
            accepted = len(occasion['accepted'])
            other = len(occasion['other'])

            if occasion['first'].occasion_cancelled:
                occasion['state'] = 'cancelled'

            elif (accepted + other) > max_spots:
                occasion['state'] = 'overfull'

            elif accepted == 0:
                occasion['state'] = 'empty'

            elif len(occasion['accepted']) < min_spots:
                occasion['state'] = 'unoperable'

            elif len(occasion['accepted']) < max_spots:
                occasion['state'] = 'operable'

            elif len(occasion['accepted']) >= max_spots:
                occasion['state'] = 'full'

            # not the most efficient way to do it, but at this time in the
            # development process a safe and convenient one
            if self.include_in_output(occasion):
                occasions[oid] = occasion

        return occasions
