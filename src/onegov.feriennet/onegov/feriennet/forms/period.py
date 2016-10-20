from cached_property import cached_property
from datetime import datetime
from onegov.activity import Activity, Period, Occasion, OccasionCollection
from onegov.feriennet import _
from onegov.form import Form
from sqlalchemy import distinct, func, or_, literal
from wtforms.fields import StringField
from wtforms.fields.html5 import DateField
from wtforms.validators import InputRequired


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
        validators=[InputRequired()]
    )

    prebooking_end = DateField(
        label=_("Prebooking End"),
        validators=[InputRequired()]
    )

    execution_start = DateField(
        label=_("Execution Start"),
        validators=[InputRequired()]
    )

    execution_end = DateField(
        label=_("Execution End"),
        validators=[InputRequired()]
    )

    @property
    def prebooking(self):
        return (self.prebooking_start.data, self.prebooking_end.data)

    @property
    def execution(self):
        return (self.execution_start.data, self.execution_end.data)

    @cached_property
    def conflicting_activites(self):
        # the model needs to be set on the form before using it - one might
        # be tempted to use a hidden field, but that might give the user the
        # ability to change the period id
        #
        # XXX add a general way to attach the model to a form if necessary
        #
        # The model may be None, (for example in a new-period form)
        assert hasattr(self, 'model')

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

        return True

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

        return True

    def validate(self):
        result = super().validate()

        ensurances = (
            self.ensure_valid_daterange_periods,
            self.ensure_no_occasion_conflicts,
        )

        for ensurance in ensurances:
            if not ensurance():
                result = False

        return result
