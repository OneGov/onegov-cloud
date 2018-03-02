from cached_property import cached_property
from datetime import datetime
from onegov.activity import Activity, Period, Occasion, OccasionDate
from onegov.activity import PeriodCollection
from onegov.core.utils import Bunch
from onegov.feriennet import _
from onegov.form import Form, merge_forms
from onegov.org.forms import ExportForm
from sqlalchemy import distinct, func, or_, literal
from wtforms.fields import StringField, RadioField, SelectField
from wtforms.fields.html5 import DateField, IntegerField, DecimalField
from wtforms.validators import InputRequired, Optional, NumberRange


class PeriodSelectForm(Form):

    period = SelectField(
        label=_("Period"),
        validators=[InputRequired()],
        default='0xdeadbeef')

    @property
    def period_choices(self):
        q = PeriodCollection(self.request.session).query()
        q = q.with_entities(Period.id, Period.title)
        q = q.order_by(Period.execution_start)

        return [(row.id.hex, row.title) for row in q]

    @property
    def selected_period(self):
        return PeriodCollection(self.request.session).by_id(
            self.period.data)

    @property
    def active_period(self):
        return self.request.app.active_period

    def on_request(self):
        self.period.choices = self.period_choices

        if self.period.data == '0xdeadbeef' and self.active_period:
            self.period.data = self.active_period.id.hex


class PeriodExportForm(merge_forms(PeriodSelectForm, ExportForm)):
    pass


class PeriodForm(Form):

    title = StringField(
        label=_("Title"),
        description=_("Ferienpass Summer ${year}", mapping={
            'year': datetime.now().year
        }),
        validators=[InputRequired()]
    )

    prebooking_start = DateField(
        label=_("Prebooking Start"),
        fieldset=_("Dates"),
        validators=[InputRequired()]
    )

    prebooking_end = DateField(
        label=_("Prebooking End"),
        fieldset=_("Dates"),
        validators=[InputRequired()]
    )

    execution_start = DateField(
        label=_("Execution Start"),
        fieldset=_("Dates"),
        validators=[InputRequired()]
    )

    execution_end = DateField(
        label=_("Execution End"),
        fieldset=_("Dates"),
        validators=[InputRequired()]
    )

    pass_system = RadioField(
        label=_("How are the activities conducted?"),
        fieldset=_("Execution"),
        choices=[
            ('no', _(
                "Each attendee may book as many activites as he likes. "
                "Each activity is billed separately."
            )),
            ('yes', _(
                "Each attendee may attend a limited number of activites "
                "for a fixed price."
            )),
        ],
        default='no',
    )

    pass_system_limit = IntegerField(
        label=_("Maximum Number of Activities per Attendee"),
        fieldset=_("Execution"),
        validators=[
            Optional(),
            NumberRange(0, 100)
        ],
        depends_on=('pass_system', 'yes')
    )

    pass_system_cost = DecimalField(
        label=_("Cost of the Pass"),
        fieldset=_("Execution"),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ],
        depends_on=('pass_system', 'yes')
    )

    single_booking_cost = DecimalField(
        label=_("The administrative cost of each booking"),
        fieldset=_("Execution"),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ],
        depends_on=('pass_system', 'no')
    )

    minutes_between = IntegerField(
        label=_("Required minutes between bookings"),
        fieldset=_("Bookings"),
        filters=(lambda x: x or 0, ),
        validators=[
            Optional(),
            NumberRange(0, 360)
        ],
        default=0
    )

    one_booking_per_day = RadioField(
        label=_("Attendees are limited to one activity per day"),
        fieldset=_("Bookings"),
        choices=[
            ('yes', _("Yes")),
            ('no', _("No"))
        ],
        default='no'
    )

    deadline = RadioField(
        label=_("Stop accepting bookings"),
        fieldset=_("Deadline"),
        choices=[
            ('fix', _("On a fixed day")),
            ('rel', _("X days before each occasion")),
        ],
        default='fix',
    )

    deadline_date = DateField(
        label=_("Fixed day"),
        fieldset=_("Deadline"),
        validators=[InputRequired()],
        depends_on=('deadline', 'fix')
    )

    deadline_days = IntegerField(
        label=_("X Days Before"),
        fieldset=_("Deadline"),
        validators=[
            InputRequired(),
            NumberRange(0, 360),
        ],
        depends_on=('deadline', 'rel')
    )

    @property
    def prebooking(self):
        return (self.prebooking_start.data, self.prebooking_end.data)

    @property
    def execution(self):
        return (self.execution_start.data, self.execution_end.data)

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'max_bookings_per_attendee',
            'booking_cost',
            'deadline_days',
            'deadline_date',
            'one_booking_per_day',
        })

        if self.pass_system.data == 'yes':
            model.max_bookings_per_attendee = self.pass_system_limit.data
            model.booking_cost = self.pass_system_cost.data
            model.all_inclusive = True
        else:
            model.max_bookings_per_attendee = None
            model.booking_cost = self.single_booking_cost.data
            model.all_inclusive = False

        if self.deadline.data == 'fix':
            model.deadline_date = self.deadline_date.data or None
            model.deadline_days = None
        else:
            model.deadline_days = self.deadline_days.data or None
            model.deadline_date = None

        if self.one_booking_per_day.data == 'yes':
            model.alignment = 'day'
        else:
            model.alignment = None

    def process_obj(self, model):
        super().process_obj(model)

        if model.all_inclusive:
            self.pass_system.data = 'yes'
            self.pass_system_limit.data = model.max_bookings_per_attendee
            self.pass_system_cost.data = model.booking_cost
        else:
            self.pass_system.data = 'no'
            self.single_booking_cost.data = model.booking_cost

        if model.deadline_days is None:
            self.deadline.data = 'fix'
        else:
            self.deadline.data = 'rel'

        if model.alignment is None:
            self.one_booking_per_day.data = 'no'
        else:
            self.one_booking_per_day.data = 'yes'

    @cached_property
    def conflicting_activities(self):
        if not isinstance(self.model, Period):
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
        )

    def ensure_no_occasion_conflicts(self):
        if self.conflicting_activities:
            msg = _("The execution phase conflicts with existing occasions")
            self.execution_start.errors.append(msg)
            self.execution_end.errors.append(msg)
            return False

    def ensure_valid_daterange_periods(self):
        fields = (
            self.prebooking_start,
            self.prebooking_end,
            self.execution_start,
            self.execution_end
        )

        stack = [fields[0]]

        for field in fields:
            if field.data is None:
                continue

            if stack.pop().data > field.data:
                field.errors.append(_(
                    "The prebooking period must start before the exeuction "
                    "period and each period must start before it ends."
                ))
                return False

            stack.append(field)

    def ensure_no_payment_changes_after_confirmation(self):
        if isinstance(self.model, Period) and self.model.confirmed:
            preview = Bunch()
            self.populate_obj(preview)

            fields = (
                'all_inclusive',
                'booking_cost'
            )

            for field in fields:
                if getattr(self.model, field) != getattr(preview, field):
                    self.pass_system.errors.append(_(
                        "It is no longer possible to change the execution "
                        "settings since the period has already been confirmed"
                    ))
                    return False

    def ensure_minutes_between_or_one_booking_per_day(self):
        if self.minutes_between.data:
            if self.one_booking_per_day.data != 'no':
                self.minutes_between.errors.append(_(
                    "It is not possible to have required minutes between "
                    "bookings when limiting attendees to one activity per day"
                ))
                return False
