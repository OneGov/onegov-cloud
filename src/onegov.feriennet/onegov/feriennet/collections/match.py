from onegov.activity import Booking, Attendee, Occasion
from onegov.core.utils import toggle
from onegov.core.orm import SQLQuery
from sqlalchemy import func
from statistics import mean


class MatchCollection(object):

    occasions_by_state = SQLQuery.from_path(
        'queries/occasions_by_state.sql', 'onegov.feriennet'
    )

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
        toggled = (
            toggle(collection, item) for collection, item in (
                (self.states, state),
            )
        )

        return self.__class__(self.session, self.period, *toggled)

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
        if self.states:
            query = self.occasions_by_state(
                period_id=self.period_id,
                states=tuple(self.states)
            )
        else:
            query = self.occasions_by_state(
                period_id=self.period_id
            )

        return self.session.execute(query)
