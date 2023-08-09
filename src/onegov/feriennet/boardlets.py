from functools import cached_property
from onegov.activity import Activity, Attendee, Booking, Occasion
from onegov.feriennet import _
from onegov.feriennet import FeriennetApp
from onegov.feriennet.collections import BillingCollection, MatchCollection
from onegov.feriennet.exports.unlucky import UnluckyExport
from onegov.feriennet.layout import DefaultLayout
from onegov.org.models import Boardlet, BoardletFact


class FeriennetBoardlet(Boardlet):

    @cached_property
    def session(self):
        return self.request.session

    @cached_property
    def period(self):
        return self.request.app.active_period

    @cached_property
    def layout(self):
        return DefaultLayout(None, self.request)

    @property
    def state(self):
        if not self.period:
            return 'failure'

        if not self.period.confirmed:
            return 'warning'

        return 'success'


@FeriennetApp.boardlet(name='period', order=(1, 1))
class PeriodBoardlet(FeriennetBoardlet):

    @property
    def title(self):
        return self.period and self.period.title or _("No active period")

    @property
    def state(self):
        if not self.period:
            return 'failure'

        return 'success'

    @property
    def facts(self):
        if not self.period:
            return

        def icon(checked):
            return 'fa-check-square-o' if checked else 'fa-square-o'

        yield BoardletFact(
            text=_("Prebooking: ${dates}", mapping={
                'dates': self.layout.format_date_range(
                    self.period.prebooking_start,
                    self.period.prebooking_end,
                )
            }),
            icon=icon(self.period.confirmed)
        )

        yield BoardletFact(
            text=_("Booking: ${dates}", mapping={
                'dates': self.layout.format_date_range(
                    self.period.booking_start,
                    self.period.booking_end,
                )
            }),
            icon=icon(self.period.is_booking_in_past)
        )

        yield BoardletFact(
            text=_("Execution: ${dates}", mapping={
                'dates': self.layout.format_date_range(
                    self.period.execution_start,
                    self.period.execution_end,
                )
            }),
            icon=icon(self.period.is_execution_in_past)
        )


@FeriennetApp.boardlet(name='activities', order=(1, 2))
class ActivitiesBoardlet(FeriennetBoardlet):

    @cached_property
    def occasions(self):
        return self.session.query(Occasion).filter_by(
            period_id=self.period.id).join(
                Activity, Occasion.activity_id == Activity.id).filter_by(
                state='accepted')

    @cached_property
    def occasions_count(self):
        if not self.period:
            return 0

        return self.occasions.count()

    @cached_property
    def activities_count(self):
        if not self.period:
            return 0

        return self.session.query(Activity).filter(Activity.id.in_(
            self.session.query(Occasion.activity_id)
                .filter_by(period_id=self.period.id)
                .subquery()
        )).filter_by(state='accepted').count()

    def occasion_states(self):
        collecion = MatchCollection(self.session, self.period)
        accepted_occasions = [a.id for a in self.occasions.all()]
        occasions = []
        for o in collecion.occasions:
            if o[1] in accepted_occasions:
                occasions.append(o[0])
        states = set(occasions)
        occasion_states = {
            'overfull': 0,
            'full': 0,
            'operable': 0,
            'unoperable': 0,
            'empty': 0,
            'cancelled': 0,
        }
        for s in states:
            occasion_states[s] = occasions.count(s)
        return occasion_states

    @property
    def title(self):
        return _("${count} Activities", mapping={
            'count': self.activities_count
        })

    @property
    def state(self):
        if not self.period:
            return 'failure'

        return self.activities_count and 'success' or 'warning'

    @property
    def facts(self):
        if not self.period:
            return

        yield BoardletFact(
            text=_("${count} Activities", mapping={
                'count': self.activities_count
            }),
            icon='fa-square'
        )

        yield BoardletFact(
            text=_("${count} Occasions", mapping={
                'count': self.occasions_count
            }),
            icon='fa-chevron-circle-down'
        )

        yield BoardletFact(
            text=_("${count} overfull", mapping={
                'count': self.occasion_states()['overfull'],
            }),
            icon='fa-exclamation-circle',
            css_class='' if self.occasion_states()['overfull'] else 'zero'
        )

        yield BoardletFact(
            text=_("${count} full", mapping={
                'count': self.occasion_states()['full'],
            }),
            icon='fa-circle',
            css_class='' if self.occasion_states()['full'] else 'zero'
        )

        yield BoardletFact(
            text=_("${count} operable", mapping={
                'count': self.occasion_states()['operable'],
            }),
            icon='fa-check-circle',
            css_class='' if self.occasion_states()['operable'] else 'zero'
        )

        yield BoardletFact(
            text=_("${count} unoperable", mapping={
                'count': self.occasion_states()['unoperable'],
            }),
            icon='fa-stop-circle',
            css_class='' if self.occasion_states()['unoperable'] else 'zero'
        )

        yield BoardletFact(
            text=_("${count} empty", mapping={
                'count': self.occasion_states()['empty'],
            }),
            icon='fa-circle-o',
            css_class='' if self.occasion_states()['empty'] else 'zero'
        )

        yield BoardletFact(
            text=_("${count} cancelled", mapping={
                'count': self.occasion_states()['cancelled'],
            }),
            icon='fa-times-circle',
            css_class='' if self.occasion_states()['cancelled'] else 'zero'
        )


@FeriennetApp.boardlet(name='bookings', order=(1, 3))
class BookingsBoardlet(FeriennetBoardlet):

    @cached_property
    def counts(self):
        if not self.period:
            return {
                'accepted': 0,
                'blocked': 0,
                'cancelled': 0,
                'denied': 0,
                'total': 0,
            }

        bookings = self.session.query(Booking)\
            .filter_by(period_id=self.period.id)

        return {
            'accepted': bookings.filter_by(state='accepted').count(),
            'blocked': bookings.filter_by(state='blocked').count(),
            'cancelled': bookings.filter_by(state='cancelled').count(),
            'denied': bookings.filter_by(state='denied').count(),
            'total': bookings.count(),
        }

    @cached_property
    def attendees_count(self):
        if not self.period:
            return 0

        return self.session.query(Attendee)\
            .filter(Attendee.id.in_(
                self.session.query(Booking.attendee_id).filter_by(
                    period_id=self.period.id
                )
            )).count()

    @property
    def title(self):
        if not self.period or not self.period.confirmed:
            return _("${count} Wishes", mapping={
                'count': self.counts['total']
            })
        else:
            return _("${count} Bookings", mapping={
                'count': self.counts['total']
            })

    @property
    def state(self):
        if not self.period:
            return 'failure'

        return self.counts['total'] and 'success' or 'warning'

    @property
    def facts(self):
        if not self.period:
            return

        if not self.period.confirmed:
            yield BoardletFact(
                text=_("${count} Wishes", mapping={
                    'count': self.counts['total']
                }),
                icon='fa-square',
            )
            yield BoardletFact(
                text=_("${count} Wishes per Attendee", mapping={
                    'count': self.attendees_count and (
                        round(self.counts['total'] / self.attendees_count, 1)
                    ) or 0
                }),
                icon='fa-line-chart',
            )
        else:
            yield BoardletFact(
                text=_("${count} Bookings", mapping={
                    'count': self.counts['total']
                }),
                icon='fa-square',
            )
            yield BoardletFact(
                text=_("${count} accepted", mapping={
                    'count': self.counts['accepted']
                }),
                icon='fa-check-square',
                css_class='' if self.counts['accepted'] else 'zero'
            )
            yield BoardletFact(
                text=_("${count} not carried out or cancelled", mapping={
                    'count': self.counts['cancelled']
                }),
                icon='fa-minus-square',
                css_class='' if self.counts['cancelled'] else 'zero'
            )
            yield BoardletFact(
                text=_("${count} denied", mapping={
                    'count': self.counts['denied']
                }),
                icon='fa-minus-square',
                css_class='' if self.counts['denied'] else 'zero'
            )
            yield BoardletFact(
                text=_("${count} blocked", mapping={
                    'count': self.counts['blocked']
                }),
                icon='fa-minus-square',
                css_class='' if self.counts['blocked'] else 'zero'
            )
            yield BoardletFact(
                text=_("${count} Bookings per Attendee", mapping={
                    'count': self.attendees_count and round(
                        self.counts['accepted'] / self.attendees_count, 1
                    ) or 0
                }),
                icon='fa-line-chart',
            )


@FeriennetApp.boardlet(name='attendees', order=(1, 4))
class AttendeesBoardlet(FeriennetBoardlet):

    @cached_property
    def attendee_counts(self):
        if not self.period:
            return {
                'total': 0,
                'female': 0,
                'male': 0,
            }

        attendee_ids = self.session.query(Booking.attendee_id).filter_by(
            period_id=self.period.id
        )

        attendees = self.session.query(Attendee).filter(
            Attendee.id.in_(attendee_ids)
        )

        accepted_attendees = self.session.query(Booking.attendee_id).filter(
            Booking.attendee_id.in_(attendee_ids),
            Booking.state == 'accepted',
            Booking.period_id == self.period.id
        ).distinct()

        return {
            'total': attendees.count(),
            'girls': attendees.filter_by(gender='female').count(),
            'boys': attendees.filter_by(gender='male').count(),
            'without_booking': attendees.count() - accepted_attendees.count()
        }

    @property
    def title(self):
        return _("${count} Attendees", mapping={
            'count': self.attendee_counts['total']
        })

    @property
    def state(self):
        if not self.period:
            return 'failure'

        return self.attendee_counts['total'] and 'success' or 'warning'

    @property
    def facts(self):
        if not self.period:
            return

        yield BoardletFact(
            text=_("${count} Girls", mapping={
                'count': self.attendee_counts['girls']
            }),
            icon='fa-female',
            css_class='' if self.attendee_counts['girls'] else 'zero'
        )

        yield BoardletFact(
            text=_("${count} Boys", mapping={
                'count': self.attendee_counts['boys']
            }),
            icon='fa-male',
            css_class='' if self.attendee_counts['boys'] else 'zero'
        )

        yield BoardletFact(
            text=_("${count} of which without accepted bookings",
                   mapping={
                       'count': self.attendee_counts['without_booking']
                   }),
            icon='fa-minus',
            css_class='' if self.attendee_counts['without_booking'] else 'zero'
        )


@FeriennetApp.boardlet(name='matching', order=(1, 5))
class MatchingBoardlet(FeriennetBoardlet):

    @cached_property
    def happiness(self):
        if not self.period or not self.period.confirmed:
            return 0

        raw = MatchCollection(self.session, self.period).happiness
        return round(raw * 100, 2)

    @cached_property
    def unlucky_count(self):
        if not self.period:
            return 0

        return UnluckyExport().query(self.session, self.period).count()

    @property
    def title(self):
        return _("${amount}% Happiness", mapping={
            'amount': self.happiness
        })

    @property
    def state(self):
        if not self.period:
            return 'failure'

        return self.happiness > 75 and 'success' or 'warning'

    @property
    def facts(self):
        if not self.period:
            return

        yield BoardletFact(
            text=_("${amount}% Happiness", mapping={
                'amount': self.happiness
            }),
            icon='fa-smile-o',
        )

        yield BoardletFact(
            text=_("${count} Attendees Without Occasion", mapping={
                'count': self.unlucky_count
            }),
            icon='fa-frown-o',
            css_class='' if self.unlucky_count else 'zero'
        )


@FeriennetApp.boardlet(name='billing', order=(1, 6))
class BillingPortlet(FeriennetBoardlet):

    @cached_property
    def amounts(self):
        if not self.period:
            return {
                'total': 0,
                'outstanding': 0,
                'paid': 0,
            }

        billing = BillingCollection(self.request, self.period)

        result = {
            'total': billing.total,
            'outstanding': billing.outstanding,
        }
        result['paid'] = result['total'] - result['outstanding']

        return result

    @property
    def title(self):
        return _("${amount} CHF outstanding", mapping={
            'amount': self.layout.format_number(self.amounts['outstanding'])
        })

    @property
    def state(self):
        if not self.period:
            return 'failure'

        return self.amounts['outstanding'] and 'warning' or 'success'

    @property
    def facts(self):
        if not self.period:
            return

        yield BoardletFact(
            text=_("${amount} CHF total", mapping={
                'amount': self.layout.format_number(self.amounts['total'])
            }),
            icon='fa-circle',
            css_class='' if self.amounts['total'] else 'zero'
        )
        yield BoardletFact(
            text=_("${amount} CHF paid", mapping={
                'amount': self.layout.format_number(self.amounts['paid'])
            }),
            icon='fa-plus-circle',
            css_class='' if self.amounts['paid'] else 'zero'
        )
        yield BoardletFact(
            text=_("${amount} CHF outstanding", mapping={
                'amount': self.layout.format_number(
                    self.amounts['outstanding']
                )
            }),
            icon='fa-minus-circle',
            css_class='' if self.amounts['outstanding'] else 'zero'
        )
