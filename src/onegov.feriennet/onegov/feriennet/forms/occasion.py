from cached_property import cached_property
from onegov.activity import Period, PeriodCollection, OccasionCollection
from onegov.feriennet import _
from onegov.form import Form
from sedate import replace_timezone
from wtforms.fields import StringField, TextAreaField, SelectField
from wtforms.fields.html5 import DateTimeField, IntegerField
from wtforms.validators import InputRequired, NumberRange
from sqlalchemy import desc


class OccasionForm(Form):

    timezone = 'Europe/Zurich'

    period_id = SelectField(
        label=_("Period"),
        validators=[InputRequired()],
        default='0xdeadbeef')

    start = DateTimeField(
        label=_("Start"),
        validators=[InputRequired()]
    )

    end = DateTimeField(
        label=_("End"),
        validators=[InputRequired()]
    )

    location = StringField(
        label=_("Location")
    )

    note = TextAreaField(
        label=_("Note"),
        render_kw={'rows': 4}
    )

    min_spots = IntegerField(
        label=_("Minimum Number of Participants"),
        validators=[
            InputRequired(),
            NumberRange(0, 10000)
        ],
        fieldset=_("Participants")
    )

    max_spots = IntegerField(
        label=_("Maximum Number of Participants"),
        validators=[
            InputRequired(),
            NumberRange(1, 10000)
        ],
        fieldset=_("Participants")
    )

    min_age = IntegerField(
        label=_("Minimum Age"),
        validators=[
            InputRequired(),
            NumberRange(0, 99)
        ],
        fieldset=_("Participants")
    )

    max_age = IntegerField(
        label=_("Maximum Age"),
        validators=[
            InputRequired(),
            NumberRange(0, 99)
        ],
        fieldset=_("Participants")
    )

    @property
    def localized_start(self):
        return replace_timezone(
            self.start.data,
            self.timezone
        )

    @property
    def localized_end(self):
        return replace_timezone(
            self.end.data,
            self.timezone
        )

    @cached_property
    def selected_period(self):
        return PeriodCollection(self.request.app.session()).by_id(
            self.period_id.data)

    def setup_period_choices(self):
        query = PeriodCollection(self.request.app.session()).query()
        query = query.order_by(desc(Period.active), Period.title)

        def choice(period):
            return str(period.id), '{} ({:%d.%m.%Y} - {:%d.%m.%Y})'.format(
                period.title,
                period.execution_start,
                period.execution_end
            )

        periods = query.all()
        self.period_id.choices = [choice(p) for p in periods]

        if self.period_id.data == '0xdeadbeef':
            self.period_id.data = periods[0].id

    def on_request(self):
        self.setup_period_choices()

    def validate(self):
        result = super().validate()

        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                self.end.errors.append(_(
                    "The end date must be after the start date"
                ))
                result = False

        if self.min_age.data and self.max_age.data:
            if self.min_age.data > self.max_age.data:
                self.min_age.errors.append(_(
                    "The minium age cannot be higher than the maximum age"
                ))
                result = False

        if self.min_spots.data and self.max_spots.data:
            if self.min_spots.data > self.max_spots.data:
                self.min_spots.errors.append(_(
                    "The minium number of participants cannot be higher "
                    "than the maximum number of participants"
                ))
                result = False

        if self.selected_period and self.start.data and self.end.data:
            execution_start = self.selected_period.execution_start
            execution_end = self.selected_period.execution_end
            start = self.start.data.date()
            end = self.start.data.date()

            if start < execution_start or execution_end < start:
                self.start.errors.append(_(
                    "The date is outside the selected period"
                ))
                result = False

            if end < execution_start or execution_end < end:
                self.end.errors.append(_(
                    "The date is outside the selected period"
                ))
                result = False

        return result

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'start',
            'end',
        })

        model.timezone = self.timezone
        model.start = self.localized_start
        model.end = self.localized_end
        model.age = OccasionCollection.to_half_open_interval(
            self.min_age.data, self.max_age.data)
        model.spots = OccasionCollection.to_half_open_interval(
            self.min_spots.data, self.max_spots.data)

    def process_obj(self, model):
        super().process_obj(model)

        self.start.data = model.localized_start
        self.end.data = model.localized_end
        self.min_age.data = model.age.lower
        self.max_age.data = model.age.upper - 1
        self.min_spots.data = model.spots.lower
        self.max_spots.data = model.spots.upper - 1
