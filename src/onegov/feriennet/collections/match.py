from __future__ import annotations

from onegov.activity import Booking, Attendee, Occasion
from onegov.core.utils import toggle
from onegov.core.orm import as_selectable_from_path
from sqlalchemy import func
from sqlalchemy import select, and_
from onegov.core.utils import module_path
from statistics import mean


from typing import Literal, NamedTuple, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection
    from datetime import datetime
    from onegov.activity.models import BookingPeriod, BookingPeriodMeta
    from sqlalchemy.orm import Query, Session
    from sqlalchemy.sql.selectable import Alias
    from typing import Self, TypeAlias
    from uuid import UUID

    class OccasionByStateRow(NamedTuple):
        state: OccasionState | None
        occasion_id: UUID
        title: str
        start: datetime
        end: datetime
        min_spots: int
        max_spots: int
        min_age: int
        max_age: int
        accepted_bookings: int
        other_bookings: int
        total_bookings: int
        period_id: UUID

OccasionState: TypeAlias = Literal[
    'cancelled',
    'overfull',
    'empty',
    'unoperable',
    'operable',
    'full'
]


class MatchCollection:

    def __init__(
        self,
        session: Session,
        period: BookingPeriod | BookingPeriodMeta,
        states: Collection[OccasionState] | None = None
    ) -> None:
        self.session = session
        self.period = period
        self.states = set(states) if states else set()

    @property
    def period_id(self) -> UUID:
        return self.period.id

    def for_period(self, period: BookingPeriod | BookingPeriodMeta) -> Self:
        return self.__class__(self.session, period)

    def for_filter(self, state: OccasionState | None = None) -> Self:
        toggled = toggle(self.states, state)
        return self.__class__(self.session, self.period, toggled)

    # FIXME: This might actually return Decimal in a query, in which case
    #        we should fix the hybrid_method
    @property
    def happiness(self) -> float:
        base = self.session.query(Attendee)
        q = base.with_entities(Attendee.happiness(self.period_id))

        values = tuple(a.happiness for a in q if a.happiness is not None)

        if values:
            return mean(values)
        else:
            return 0

    @property
    def occasions_by_state(self) -> Alias:
        return as_selectable_from_path(
            module_path('onegov.feriennet', 'queries/occasions_by_state.sql'))

    @property
    def operability(self) -> float:
        accepted = (
            self.session.query(func.count(Booking.id).label('count'))
            .filter(Booking.occasion_id == Occasion.id)
            .filter(Booking.period_id == self.period_id)
            .filter(Booking.state == 'accepted')
            .subquery().lateral()
        )

        o = self.session.query(Occasion.spots, accepted.c.count)
        o = o.filter(Occasion.period_id == self.period_id)

        bits = [
            1 if count >= spots.lower else 0
            for spots, count in o
        ]

        if not bits:
            return 0

        return sum(bits) / len(bits)

    def include_in_output(self, occasion: OccasionByStateRow) -> bool:
        if not self.states:
            return True

        return occasion.state in self.states

    @property
    def occasions(self) -> Query[OccasionByStateRow]:
        columns = self.occasions_by_state.c
        query = select(columns)

        if not self.states:
            query = query.where(columns.period_id == self.period_id)
        else:
            query = query.where(and_(
                columns.period_id == self.period_id,
                columns.state.in_(self.states)
            ))

        query = query.order_by(columns.title, columns.start)

        return self.session.execute(query)
