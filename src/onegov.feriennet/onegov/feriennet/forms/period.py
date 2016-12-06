from cached_property import cached_property
from datetime import datetime
from onegov.activity import Activity, Period, Occasion, OccasionCollection
from onegov.core.utils import Bunch
from onegov.feriennet import _
from onegov.form import Form
from sqlalchemy import distinct, func, or_, literal
from wtforms.fields import StringField, RadioField
from wtforms.fields.html5 import DateField, IntegerField, DecimalField
from wtforms.validators import InputRequired, Optional, NumberRange


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
        label=_("Pass System"),
        fieldset=_("Execution Settings"),
        choices=[
            ('no', _("Each attendee may book as many activites as he likes")),
            ('yes', _("Each attendee may attend a fixed number of activites")),
        ],
        default='no',
    )

    pass_system_limit = IntegerField(
        label=_("Maximum Number of Activities per Attendee"),
        fieldset=_("Execution Settings"),
        validators=[
            Optional(),
            NumberRange(0, 100)
        ],
        depends_on=('pass_system', 'yes')
    )

    pass_system_cost = DecimalField(
        label=_("Cost of the Pass"),
        fieldset=_("Execution Settings"),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ],
        depends_on=('pass_system', 'yes')
    )

    single_booking_cost = DecimalField(
        label=_("The administrative cost of each booking"),
        fieldset=_("Execution Settings"),
        validators=[
            Optional(),
            NumberRange(0.00, 10000.00)
        ],
        depends_on=('pass_system', 'no')
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
            'booking_cost'
        })

        if self.pass_system.data == 'yes':
            model.max_bookings_per_attendee = self.pass_system_limit.data
            model.booking_cost = self.pass_system_cost.data
            model.all_inclusive = True
        else:
            model.max_bookings_per_attendee = None
            model.booking_cost = self.single_booking_cost.data
            model.all_inclusive = False

    def process_obj(self, model):
        super().process_obj(model)

        if model.all_inclusive:
            self.pass_system.data = 'yes'
            self.pass_system_limit.data = model.max_bookings_per_attendee
            self.pass_system_cost.data = model.booking_cost
        else:
            self.pass_system.data = 'no'
            self.single_booking_cost.data = model.booking_cost

    @cached_property
    def conflicting_activites(self):
        if not isinstance(self.model, Period):
            return None

        session = self.request.app.session()

        mindate = self.execution_start.data
        maxdate = self.execution_end.data

        # turn naive utc to aware utc to local timezone
        occasion_start = Occasion.start.op('AT TIME ZONE')(literal('UTC'))
        occasion_start = occasion_start.op('AT TIME ZONE')(Occasion.timezone)
        occasion_end = Occasion.end.op('AT TIME ZONE')(literal('UTC'))
        occasion_end = occasion_end.op('AT TIME ZONE')(Occasion.timezone)

        query = OccasionCollection(session).query()
        query = query.with_entities(distinct(Occasion.activity_id))
        query = query.filter(Occasion.period == self.model)
        query = query.filter(or_(
            func.date_trunc('day', occasion_start) < mindate,
            func.date_trunc('day', occasion_start) > maxdate,
            func.date_trunc('day', occasion_end) < mindate,
            func.date_trunc('day', occasion_end) > maxdate
        ))

        query = session.query(Activity).filter(
            Activity.id.in_(query.subquery()))

        return query.all()

    def ensure_no_occasion_conflicts(self):
        if self.conflicting_activites:
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
                'booking_cost',
                'max_bookings_per_attendee',
            )

            for field in fields:
                if getattr(self.model, field) != getattr(preview, field):
                    self.pass_system.errors.append(_(
                        "It is no longer possible to change the execution "
                        "settings since the period has already been confirmed"
                    ))
                    return False
