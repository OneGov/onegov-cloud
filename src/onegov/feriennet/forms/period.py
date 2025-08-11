from __future__ import annotations

from functools import cached_property
from datetime import date, datetime
from onegov.activity import Activity, BookingPeriod, Occasion, OccasionDate
from onegov.activity import BookingPeriodCollection
from onegov.core.utils import Bunch
from onegov.feriennet import _
from onegov.form import Form, merge_forms
from onegov.form.fields import PanelField
from onegov.org.forms import ExportForm
from sqlalchemy import distinct, func, or_, literal
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.fields import SelectField
from wtforms.fields import StringField
from wtforms.validators import InputRequired, Optional, NumberRange


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models import BookingPeriodMeta
    from onegov.feriennet.request import FeriennetRequest
    from wtforms.fields.choices import _Choice


class PeriodSelectForm(Form):

    request: FeriennetRequest

    period = SelectField(
        label=_('Period'),
        validators=[InputRequired()],
        default='0xdeadbeef')

    @property
    def period_choices(self) -> list[_Choice]:
        q = BookingPeriodCollection(self.request.session).query()
        q = q.with_entities(BookingPeriod.id, BookingPeriod.title)
        q = q.order_by(BookingPeriod.execution_start)

        return [(row.id.hex, row.title) for row in q]

    @property
    def selected_period(self) -> BookingPeriod | None:
        return BookingPeriodCollection(self.request.session).by_id(
            self.period.data)

    @property
    def active_period(self) -> BookingPeriodMeta | None:
        return self.request.app.active_period

    def on_request(self) -> None:
        self.period.choices = self.period_choices

        if self.period.data == '0xdeadbeef' and self.active_period:
            self.period.data = self.active_period.id.hex


if TYPE_CHECKING:
    class PeriodExportForm(PeriodSelectForm, ExportForm):
        pass
else:
    class PeriodExportForm(merge_forms(PeriodSelectForm, ExportForm)):
        pass


class PeriodForm(Form):

    title = StringField(
        label=_('Title'),
        description=_('Ferienpass Summer ${year}', mapping={
            'year': datetime.now().year
        }),
        validators=[InputRequired()]
    )

    confirmable = BooleanField(
        label=_('With pre-booking phase'),
        default=True
    )

    unconfirmable_warning = PanelField(
        text=_(
            'A period that is started without pre-booking phase cannot be '
            'turned into a period with pre-booking phase later. If in doubt, '
            'use the pre-booking phase and confirm it manually.'
        ),
        kind='callout',
        depends_on=('confirmable', '!y')
    )

    finalizable = BooleanField(
        label=_('With billing'),
        default=True
    )

    unfinalizable_warning = PanelField(
        text=_(
            "A period without billing will hide all bills from regular users, "
            "so if you have used billing before and have open bills, your "
            "users won't find them. If in doubt, use billing without creating "
            "any bills."
        ),
        kind='callout',
        depends_on=('finalizable', '!y')
    )

    prebooking_start = DateField(
        label=_('Prebooking Start'),
        fieldset=_('Dates'),
        validators=[InputRequired()],
        depends_on=('confirmable', 'y'),
    )

    prebooking_end = DateField(
        label=_('Prebooking End'),
        fieldset=_('Dates'),
        validators=[InputRequired()],
        depends_on=('confirmable', 'y'),
    )

    booking_start = DateField(
        label=_('Booking Start'),
        fieldset=_('Dates'),
        validators=[InputRequired()]
    )

    booking_end = DateField(
        label=_('Booking End'),
        fieldset=_('Dates'),
        validators=[InputRequired()]
    )

    execution_start = DateField(
        label=_('Execution Start'),
        fieldset=_('Dates'),
        validators=[InputRequired()]
    )

    execution_end = DateField(
        label=_('Execution End'),
        fieldset=_('Dates'),
        validators=[InputRequired()]
    )

    pass_system = RadioField(
        label=_('How are the activities conducted?'),
        fieldset=_('Execution'),
        choices=[
            ('no', _(
                'Each attendee may book as many activites as he likes. '
                'Each activity is billed separately.'
            )),
            ('yes', _(
                'Each attendee may attend a limited number of activites '
                'for a fixed price.'
            )),
            ('fixed', _(
                'Each attendee may attend a fixed number of activites. '
                'Each activity is billed separately.'
            )),
        ],
        default='no',
    )

    pass_system_limit = IntegerField(
        label=_('Maximum Number of Activities per Attendee'),
        fieldset=_('Execution'),
        validators=[
            Optional(),
            NumberRange(0, 100)
        ],
        depends_on=('pass_system', 'yes')
    )

    fixed_system_limit = IntegerField(
        label=_('Maximum Number of Bookings per Attendee and period'),
        fieldset=_('Execution'),
        validators=[
            Optional(),
            NumberRange(0, 100)
        ],
        depends_on=('pass_system', 'fixed')
    )

    pass_system_cost = DecimalField(
        label=_('Cost of the Pass'),
        fieldset=_('Execution'),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ],
        depends_on=('pass_system', 'yes')
    )

    single_booking_cost = DecimalField(
        label=_('The administrative cost of each booking'),
        fieldset=_('Execution'),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ],
        depends_on=('pass_system', '!yes')
    )

    pay_organiser_directly = RadioField(
        label=_('How is the organiser paid?'),
        fieldset=_('Execution'),
        choices=[
            ('indirect', _(
                'The parents pay everything by bill, '
                'the organisers are paid later'
            )),
            ('direct', _(
                'The parents pay the pass by bill, the organisers are paid in '
                'cash at the beginning of each occasion'
            ))
        ],
        default='indirect',
        depends_on=('pass_system', 'yes')
    )

    minutes_between = IntegerField(
        label=_('Required minutes between bookings'),
        fieldset=_('Bookings'),
        filters=(lambda x: x or 0, ),
        validators=[
            Optional(),
            NumberRange(0, 360)
        ],
        default=0
    )

    one_booking_per_day = RadioField(
        label=_('Attendees are limited to one activity per day'),
        fieldset=_('Bookings'),
        choices=[
            ('yes', _('Yes')),
            ('no', _('No'))
        ],
        default='no'
    )

    deadline = RadioField(
        label=_('Stop accepting bookings'),
        fieldset=_('Deadline'),
        choices=[
            ('fix', _('At the end of the booking phase')),
            ('rel', _('X days before each occasion')),
        ],
        default='fix',
    )

    deadline_days = IntegerField(
        label=_('X Days Before'),
        fieldset=_('Deadline'),
        validators=[
            InputRequired(),
            NumberRange(0, 360),
        ],
        depends_on=('deadline', 'rel')
    )

    book_finalized = BooleanField(
        label=_('Allow bookings after the bills have been created.'),
        description=_(
            'By default, only admins can create bookings after the billing '
            'has been confirmed. With this setting, every user can create new '
            'bookings after confirmation and before the deadline. Booking '
            'costs incurred after confirmation will be added to the existing '
            'bill.'
        ),
        depends_on=('deadline', 'rel'),
    )

    cancellation = RadioField(
        label=_('Allow members to cancel confirmed bookings'),
        fieldset=_('Cancellation Deadline'),
        choices=[
            ('no', _('No, only allow admins')),
            ('fix', _('Until a fixed day')),
            ('rel', _('Up to X days before each occasion')),
        ],
        default='no',
    )

    cancellation_date = DateField(
        label=_('Fixed day'),
        fieldset=_('Cancellation Deadline'),
        validators=[InputRequired()],
        depends_on=('cancellation', 'fix')
    )

    cancellation_days = IntegerField(
        label=_('X Days Before'),
        fieldset=_('Cancellation Deadline'),
        validators=[
            InputRequired(),
            NumberRange(0, 360),
        ],
        depends_on=('cancellation', 'rel')
    )

    age_barrier_type = RadioField(
        label=_('Method'),
        fieldset=_('Age check'),
        choices=[
            ('exact', _(
                'Exact - the attendees need to be of the expected age '
                'at the beginning of the occasion'
            )),
            ('year', _(
                'Age group - The attendees need to be of the expected '
                'age sometime during the year of the occasion'
            )),
        ],
        default='exact'
    )

    @property
    def prebooking(self) -> tuple[date | None, date | None]:
        return self.prebooking_start.data, self.prebooking_end.data

    @property
    def booking(self) -> tuple[date | None, date | None]:
        return self.booking_start.data, self.booking_end.data

    @property
    def execution(self) -> tuple[date | None, date | None]:
        return self.execution_start.data, self.execution_end.data

    @property
    def is_new(self) -> bool:
        return isinstance(self.model, BookingPeriodCollection)

    def on_request(self) -> None:

        # disable the 'confirmable' flag on existing periods
        if not self.is_new:
            self.confirmable.render_kw = self.confirmable.render_kw or {}
            self.confirmable.render_kw['disabled'] = ''

    def validate(self) -> bool:  # type:ignore[override]
        # prevent any changes to the 'confirmable' property after creation
        if not self.is_new:
            self.confirmable.data = self.model.confirmable
        return super().validate()

    def populate_obj(self, model: BookingPeriod) -> None:  # type:ignore[override]
        adjust_defaults = model.booking_start != self.booking_start.data
        also_exclude: tuple[str, ...]
        if not self.confirmable.data and not adjust_defaults:
            also_exclude = ('prebooking_start', 'prebooking_end')
        else:
            also_exclude = ()

        super().populate_obj(model, exclude={
            'max_bookings_per_attendee',
            'booking_cost',
            'deadline_days',
            'one_booking_per_day',
            'pay_organiser_directly',
            'cancellation_date',
            'cancellation_days',

            # excluded here and not used later, only has an effect when
            # the period is added through the new period view
            'confirmable',

            *also_exclude,
        })

        if self.pass_system.data == 'yes':
            model.max_bookings_per_attendee = self.pass_system_limit.data
            model.booking_cost = self.pass_system_cost.data
            model.all_inclusive = True
        elif self.pass_system.data == 'no':
            model.max_bookings_per_attendee = None
            model.booking_cost = self.single_booking_cost.data
            model.all_inclusive = False
        elif self.pass_system.data == 'fixed':
            model.max_bookings_per_attendee = self.fixed_system_limit.data
            model.booking_cost = self.single_booking_cost.data
            model.all_inclusive = False

        if self.deadline.data == 'fix':
            model.deadline_days = None
            model.book_finalized = False
        else:
            model.deadline_days = self.deadline_days.data or None
            model.book_finalized = self.book_finalized.data

        if self.cancellation.data == 'no':
            model.cancellation_date = None
            model.cancellation_days = None
        elif self.cancellation.data == 'fix':
            model.cancellation_date = self.cancellation_date.data
            model.cancellation_days = None
        elif self.cancellation.data == 'rel':
            model.cancellation_days = self.cancellation_days.data
            model.cancellation_date = None

        if self.one_booking_per_day.data == 'yes':
            model.alignment = 'day'
        else:
            model.alignment = None

        if self.pass_system.data in ('no', 'fixed'):
            model.pay_organiser_directly = False
        elif self.pay_organiser_directly.data == 'direct':
            model.pay_organiser_directly = True
        else:
            model.pay_organiser_directly = False

    def process_obj(self, model: BookingPeriod) -> None:  # type:ignore[override]
        super().process_obj(model)

        if model.all_inclusive:
            self.pass_system.data = 'yes'
            self.pass_system_limit.data = model.max_bookings_per_attendee
            self.pass_system_cost.data = model.booking_cost
        else:
            self.single_booking_cost.data = model.booking_cost

            if model.max_bookings_per_attendee is None:
                self.pass_system.data = 'no'
            else:
                self.pass_system.data = 'fixed'
                self.fixed_system_limit.data = model.max_bookings_per_attendee

        if model.deadline_days is None:
            self.deadline.data = 'fix'
            self.book_finalized.data = False
        else:
            self.deadline.data = 'rel'
            self.book_finalized.data = model.book_finalized

        if model.cancellation_days is None and model.cancellation_date is None:
            self.cancellation.data = 'no'
        elif model.cancellation_days is not None:
            self.cancellation.data = 'rel'
            self.cancellation_days.data = model.cancellation_days
        else:
            self.cancellation.data = 'fix'
            self.cancellation_date.data = model.cancellation_date

        if model.alignment is None:
            self.one_booking_per_day.data = 'no'
        else:
            self.one_booking_per_day.data = 'yes'

        if model.pay_organiser_directly:
            self.pay_organiser_directly.data = 'direct'
        else:
            self.pay_organiser_directly.data = 'indirect'

    @cached_property
    def conflicting_activities(self) -> tuple[Activity, ...] | None:
        if not isinstance(self.model, BookingPeriod):
            return None

        session = self.request.session

        mindate = self.execution_start.data
        maxdate = self.execution_end.data

        if not (mindate and maxdate):
            return None

        # turn naive utc to aware utc to local timezone
        start = OccasionDate.start.op('AT TIME ZONE')(literal('UTC'))
        start = start.op('AT TIME ZONE')(OccasionDate.timezone)
        end = OccasionDate.end.op('AT TIME ZONE')(literal('UTC'))
        end = end.op('AT TIME ZONE')(OccasionDate.timezone)

        qd = session.query(OccasionDate)
        qd = qd.with_entities(OccasionDate.occasion_id)
        qd = qd.filter(or_(
            func.date_trunc('day', start) < mindate,
            func.date_trunc('day', start) > maxdate,
            func.date_trunc('day', end) < mindate,
            func.date_trunc('day', end) > maxdate
        ))

        q = session.query(OccasionDate).join(Occasion)
        q = q.with_entities(distinct(Occasion.activity_id))
        q = q.filter(Occasion.period == self.model)
        q = q.filter(Occasion.id.in_(qd.subquery()))

        return tuple(
            session.query(Activity).filter(Activity.id.in_(q.subquery()))
            .order_by(Activity.order)
        )

    def ensure_dependant_fields_empty(self) -> None:
        if self.is_new and self.confirmable.data is False:
            self.prebooking_start.data = None
            self.prebooking_end.data = None

    def ensure_hidden_fields_changed(self) -> None:
        if self.is_new:
            return
        if not self.model.confirmable:
            self.prebooking_start.data = self.booking_start.data
            self.prebooking_end.data = self.booking_start.data

    def ensure_no_occasion_conflicts(self) -> bool | None:
        if self.conflicting_activities:
            msg = _('The execution phase conflicts with existing occasions')
            assert isinstance(self.execution_start.errors, list)
            assert isinstance(self.execution_end.errors, list)
            self.execution_start.errors.append(msg)
            self.execution_end.errors.append(msg)
            return False
        return None

    def ensure_valid_daterange_periods(self) -> bool | None:
        if self.prebooking_start.data and self.prebooking_end.data:
            if self.prebooking_start.data > self.prebooking_end.data:
                assert isinstance(self.prebooking_start.errors, list)
                self.prebooking_start.errors.append(_(
                    'Prebooking must start before it ends'))
                return False

        if self.booking_start.data and self.booking_end.data:
            if self.booking_start.data > self.booking_end.data:
                assert isinstance(self.booking_start.errors, list)
                self.booking_start.errors.append(_(
                    'Booking must start before it ends'))
                return False

        if self.execution_start.data and self.execution_end.data:
            if self.execution_start.data > self.execution_end.data:
                assert isinstance(self.execution_start.errors, list)
                self.execution_start.errors.append(_(
                    'Execution must start before it ends'))
                return False

        if self.prebooking_end.data and self.booking_start.data:
            if self.prebooking_end.data > self.booking_start.data:
                assert isinstance(self.prebooking_end.errors, list)
                self.prebooking_end.errors.append(_(
                    'Prebooking must end before booking starts'))
                return False

        if self.prebooking_end.data and self.execution_start.data:
            if self.prebooking_end.data > self.execution_start.data:
                assert isinstance(self.prebooking_end.errors, list)
                self.prebooking_end.errors.append(_(
                    'Prebooking must end before execution starts'))
                return False

        if self.booking_start.data and self.execution_start.data:
            if self.booking_start.data > self.execution_start.data:
                assert isinstance(self.execution_start.errors, list)
                self.execution_start.errors.append(_(
                    'Execution may not start before booking starts'))
                return False

        if self.booking_end.data and self.execution_end.data:
            if self.booking_end.data > self.execution_end.data:
                assert isinstance(self.execution_end.errors, list)
                self.execution_end.errors.append(_(
                    'Execution may not end before booking ends'))
                return False
        return None

    def ensure_no_payment_changes_after_confirmation(self) -> bool | None:
        if isinstance(self.model, BookingPeriod) and self.model.confirmed:
            preview: Any = Bunch(
                confirmable=self.model.confirmable,
                booking_start=self.model.booking_start
            )
            self.populate_obj(preview)

            fields = (
                'all_inclusive',
                'booking_cost'
            )

            for field in fields:
                if getattr(self.model, field) != getattr(preview, field):
                    assert isinstance(self.pass_system.errors, list)
                    self.pass_system.errors.append(_(
                        'It is no longer possible to change the execution '
                        'settings since the period has already been confirmed.'
                    ))
                    return False
        return None

    def ensure_minutes_between_or_one_booking_per_day(self) -> bool | None:
        if self.minutes_between.data:
            if self.one_booking_per_day.data != 'no':
                assert isinstance(self.minutes_between.errors, list)
                self.minutes_between.errors.append(_(
                    'It is not possible to have required minutes between '
                    'bookings when limiting attendees to one activity per day.'
                ))
                return False
        return None
