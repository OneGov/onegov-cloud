from __future__ import annotations

from decimal import Decimal
from functools import cached_property
from onegov.activity import Activity, Attendee, Booking, Occasion
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import BillingCollection, MatchCollection
from onegov.feriennet.exports.unlucky import UnluckyExport
from onegov.feriennet.layout import DefaultLayout
from onegov.org.boardlets import (
    EditedTopicsBoardlet, EditedNewsBoardlet, PlausibleStats,
    PlausibleTopPages, TicketBoardlet)
from onegov.org.models import Boardlet, BoardletFact
from sqlalchemy import func


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.activity.models import BookingPeriodMeta
    from onegov.activity.models.booking import BookingState
    from onegov.feriennet.collections.match import OccasionState
    from onegov.feriennet.request import FeriennetRequest
    from sqlalchemy.orm import Query, Session


class FeriennetBoardlet(Boardlet):

    request: FeriennetRequest

    @cached_property
    def session(self) -> Session:
        return self.request.session

    @cached_property
    def period(self) -> BookingPeriodMeta | None:
        return self.request.app.active_period

    @cached_property
    def layout(self) -> DefaultLayout:
        return DefaultLayout(None, self.request)

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        if not self.period:
            return 'failure'

        if not self.period.confirmed:
            return 'warning'

        return 'success'


@FeriennetApp.boardlet(name='ticket', order=(1, 1), icon='fa-ticket-alt')
class DisabledTicketBoardlet(TicketBoardlet):

    @property
    def is_available(self) -> bool:
        return False


@FeriennetApp.boardlet(name='pages', order=(1, 2), icon='fa-edit')
class DisabledEditedPagesBoardlet(EditedTopicsBoardlet):

    @property
    def is_available(self) -> bool:
        return False


@FeriennetApp.boardlet(name='news', order=(1, 3), icon='fa-edit')
class DisabledEditedNewsBoardlet(EditedNewsBoardlet):

    @property
    def is_available(self) -> bool:
        return False


@FeriennetApp.boardlet(name='web stats', order=(2, 1))
class DisabledPlausibleStats(PlausibleStats):

    @property
    def is_available(self) -> bool:
        return False


@FeriennetApp.boardlet(name='most popular pages', order=(2, 2))
class DisabledPlausibleTopPages(PlausibleTopPages):

    @property
    def is_available(self) -> bool:
        return False


@FeriennetApp.boardlet(name='period', order=(1, 1))
class PeriodBoardlet(FeriennetBoardlet):

    @property
    def title(self) -> str:
        return self.period and self.period.title or _('No active period')

    @property
    def state(self) -> Literal['success', 'failure']:
        if not self.period:
            return 'failure'

        return 'success'

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.period:
            return

        def icon(checked: bool) -> str:
            return 'far fa-check-circle' if checked else 'far fa-circle'

        yield BoardletFact(
            text=_('Prebooking: ${dates}', mapping={
                'dates': self.layout.format_date_range(
                    self.period.prebooking_start,
                    self.period.prebooking_end,
                )
            }),
            icon=icon(self.period.confirmed),
        )

        yield BoardletFact(
            text=_('Booking: ${dates}', mapping={
                'dates': self.layout.format_date_range(
                    self.period.booking_start,
                    self.period.booking_end,
                )
            }),
            icon=icon(self.period.is_booking_in_past),
        )

        yield BoardletFact(
            text=_('Execution: ${dates}', mapping={
                'dates': self.layout.format_date_range(
                    self.period.execution_start,
                    self.period.execution_end,
                )
            }),
            icon=icon(self.period.is_execution_in_past),
        )


@FeriennetApp.boardlet(name='activities', order=(1, 2))
class ActivitiesBoardlet(FeriennetBoardlet):

    @cached_property
    def occasions(self) -> Query[Occasion]:
        assert self.period is not None
        return self.session.query(Occasion).filter_by(
            period_id=self.period.id).join(
                Activity, Occasion.activity_id == Activity.id).filter_by(
                state='accepted')

    @cached_property
    def occasions_count(self) -> int:
        if not self.period:
            return 0

        return self.occasions.with_entities(func.count(Occasion.id)).scalar()

    @cached_property
    def activities_count(self) -> int:
        if not self.period:
            return 0

        return self.session.query(func.count(Activity.id)).filter(
            Activity.id.in_(
                self.session.query(Occasion.activity_id)
                .filter_by(period_id=self.period.id)
                .scalar_subquery()
            )
        ).filter_by(state='accepted').scalar()

    def occasion_states(self) -> dict[OccasionState, int]:
        occasion_states: dict[OccasionState, int] = {
            'overfull': 0,
            'full': 0,
            'operable': 0,
            'unoperable': 0,
            'empty': 0,
            'cancelled': 0,
        }
        if self.period is None:
            return occasion_states

        # FIXME: We should try to do the filtering, grouping, counting
        #        in SQL, we just have to restructure things a bit so
        #        we can modify the query or use it as a subquery
        collection = MatchCollection(self.session, self.period)
        accepted_occasions = [a.id for a in self.occasions]
        occasions = [
            o.state
            for o in collection.occasions
            if o.occasion_id in accepted_occasions
        ]
        states = set(occasions)
        for s in states:
            if s is None:
                continue
            occasion_states[s] = occasions.count(s)
        return occasion_states

    @property
    def title(self) -> str:
        return _('Activities')

    @property
    def number(self) -> int:
        return self.activities_count

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        if not self.period:
            return 'failure'

        return self.activities_count and 'success' or 'warning'

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.period:
            return

        yield BoardletFact(
            text=_('Activities'),
            number=self.activities_count
        )

        yield BoardletFact(
            text=_('Occasions'),
            number=self.occasions_count
        )

        states = self.occasion_states()

        yield BoardletFact(
            text=_('overfull'),
            number=states['overfull'],
            css_class='' if states['overfull'] else 'zero'
        )

        yield BoardletFact(
            text=_('full'),
            number=states['full'],
            css_class='' if states['full'] else 'zero'
        )

        yield BoardletFact(
            text=_('operable'),
            number=states['operable'],
            css_class='' if states['operable'] else 'zero'
        )

        yield BoardletFact(
            text=_('unoperable'),
            number=states['unoperable'],
            css_class='' if states['unoperable'] else 'zero'
        )

        yield BoardletFact(
            text=_('empty'),
            number=states['empty'],
            css_class='' if states['empty'] else 'zero'
        )

        yield BoardletFact(
            text=_('cancelled'),
            number=states['cancelled'],
            css_class='' if states['cancelled'] else 'zero'
        )


@FeriennetApp.boardlet(name='bookings', order=(1, 3))
class BookingsBoardlet(FeriennetBoardlet):

    @cached_property
    def counts(self) -> dict[BookingState | Literal['total'], int]:
        counts: dict[BookingState | Literal['total'], int] = {
            'accepted': 0,
            'blocked': 0,
            'cancelled': 0,
            'denied': 0,
            'total': 0,
        }
        if not self.period:
            return counts

        query = (
            self.session.query(Booking.state, func.count(Booking.id))
            .filter_by(period_id=self.period.id)
            .group_by(Booking.state)
        )

        for state, count in query:
            counts['total'] += count
            if state in counts:
                counts[state] = count

        return counts

    @cached_property
    def attendees_count(self) -> int:
        if not self.period:
            return 0

        # NOTE: This works because Booking.attendee_id is not nullable
        return self.session.query(
            func.count(Booking.attendee_id.distinct())
        ).filter_by(period_id=self.period.id).scalar()

    @property
    def title(self) -> str:
        if not self.period or not self.period.confirmed:
            return _('Wishes')
        else:
            return _('Bookings')

    @property
    def number(self) -> int:
        return self.counts['total']

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        if not self.period:
            return 'failure'

        return self.counts['total'] and 'success' or 'warning'

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.period:
            return

        if not self.period.confirmed:
            yield BoardletFact(
                text=_('Wishes'),
                number=str(self.counts['total'])
            )
            yield BoardletFact(
                text=_('Wishes per Attendee'),
                number=self.attendees_count and (
                    round(self.counts['total'] / self.attendees_count, 1)
                ) or 0
            )
        else:
            yield BoardletFact(
                text=_('Bookings'),
                number=self.counts['total']
            )
            yield BoardletFact(
                text=_('accepted'),
                number=self.counts['accepted'],
                css_class='' if self.counts['accepted'] else 'zero'
            )
            yield BoardletFact(
                text=_('not carried out or cancelled'),
                number=self.counts['cancelled'],
                css_class='' if self.counts['cancelled'] else 'zero'
            )
            yield BoardletFact(
                text=_('denied'),
                number=self.counts['denied'],
                css_class='' if self.counts['denied'] else 'zero'
            )
            yield BoardletFact(
                text=_('blocked'),
                number=self.counts['blocked'],
                css_class='' if self.counts['blocked'] else 'zero'
            )
            yield BoardletFact(
                text=_('Bookings per Attendee'),
                number=self.attendees_count and round(
                        self.counts['accepted'] / self.attendees_count, 1
                    ) or 0,
            )


@FeriennetApp.boardlet(name='attendees', order=(1, 4))
class AttendeesBoardlet(FeriennetBoardlet):

    @cached_property
    def attendee_counts(self) -> dict[str, int]:
        counts = {
            'total': 0,
            'girls': 0,
            'boys': 0,
            'without_booking': 0
        }
        if not self.period:
            return counts

        query = self.session.query(
            Attendee.gender,
            func.count(Attendee.id),
        ).filter(Attendee.id.in_(
            self.session.query(Booking.attendee_id)
            .filter_by(period_id=self.period.id)
            .scalar_subquery()
        )).group_by(Attendee.gender)

        for gender, count in query:
            counts['total'] += count
            if gender == 'male':
                counts['boys'] = count
            elif gender == 'female':
                counts['girls'] = count

        accepted_attendees = self.session.query(
            func.count(Booking.attendee_id.distinct())
        ).filter(
            Booking.state == 'accepted',
            Booking.period_id == self.period.id
        ).scalar()

        counts['without_booking'] = counts['total'] - accepted_attendees
        return counts

    @property
    def title(self) -> str:
        return _('Attendees')

    @property
    def number(self) -> int:
        return self.attendee_counts['total']

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        if not self.period:
            return 'failure'

        return self.attendee_counts['total'] and 'success' or 'warning'

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.period:
            return

        yield BoardletFact(
            text=_('Girls'),
            number=self.attendee_counts['girls'],
            css_class='' if self.attendee_counts['girls'] else 'zero'
        )

        yield BoardletFact(
            text=_('Boys'),
            number=self.attendee_counts['boys'],
            css_class='' if self.attendee_counts['boys'] else 'zero'
        )

        yield BoardletFact(
            text=_('of which without accepted bookings'),
            number=self.attendee_counts['without_booking'],
            css_class='' if self.attendee_counts['without_booking'] else 'zero'
        )


@FeriennetApp.boardlet(name='matching', order=(1, 5))
class MatchingBoardlet(FeriennetBoardlet):

    @cached_property
    def happiness(self) -> float:
        if not self.period or not self.period.confirmed:
            return 0

        raw = MatchCollection(self.session, self.period).happiness
        return round(raw * 100, 2)

    @cached_property
    def unlucky_count(self) -> int:
        if not self.period:
            return 0

        return UnluckyExport().query(self.session, self.period).count()

    @property
    def title(self) -> str:
        return _('Happiness')

    @property
    def number(self) -> str:
        return f'{self.happiness}%'

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        if not self.period:
            return 'failure'

        return self.happiness > 75 and 'success' or 'warning'

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.period:
            return

        yield BoardletFact(
            text=_('Attendees Without Occasion'),
            number=str(self.unlucky_count),
            css_class='' if self.unlucky_count else 'zero'
        )


@FeriennetApp.boardlet(name='billing', order=(1, 6))
class BillingPortlet(FeriennetBoardlet):

    @cached_property
    def amounts(self) -> dict[str, Decimal]:
        if not self.period:
            return {
                'total': Decimal(0),
                'outstanding': Decimal(0),
                'paid': Decimal(0),
            }

        billing = BillingCollection(self.request, self.period)

        result = {
            'total': billing.total,
            'outstanding': billing.outstanding,
        }
        result['paid'] = result['total'] - result['outstanding']

        return result

    @property
    def title(self) -> str:
        return _('CHF outstanding')

    @property
    def number(self) -> str:
        return self.layout.format_number(self.amounts['outstanding'])

    @property
    def state(self) -> Literal['success', 'warning', 'failure']:
        if not self.period:
            return 'failure'

        return self.amounts['outstanding'] and 'warning' or 'success'

    @property
    def facts(self) -> Iterator[BoardletFact]:
        if not self.period:
            return

        yield BoardletFact(
            text=_('CHF total'),
            number=self.layout.format_number(self.amounts['total']),
            css_class='' if self.amounts['total'] else 'zero'
        )
        yield BoardletFact(
            text=_('CHF paid'),
            number=self.layout.format_number(self.amounts['paid']),
            css_class='' if self.amounts['paid'] else 'zero'
        )
        yield BoardletFact(
            text=_('CHF outstanding'),
            number=self.layout.format_number(self.amounts['outstanding']),
            css_class='' if self.amounts['outstanding'] else 'zero'
        )
