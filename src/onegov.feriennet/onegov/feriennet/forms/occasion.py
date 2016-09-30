from datetime import datetime
from onegov.feriennet import _
from onegov.form import Form
from sedate import replace_timezone, utcnow
from wtforms.fields import StringField
from wtforms.fields.html5 import DateField, IntegerField
from wtforms.validators import InputRequired, NumberRange
from wtforms_components import TimeField


class OccasionForm(Form):

    timezone = 'Europe/Zurich'

    start_date = DateField(
        label=_("Start Date"),
        validators=[InputRequired()]
    )

    start_time = TimeField(
        label=_("Start Time"),
        description="09:00",
        validators=[InputRequired()]
    )

    end_date = DateField(
        label=_("End Date"),
        validators=[InputRequired()]
    )

    end_time = TimeField(
        label=_("End Time"),
        description="18:00",
        validators=[InputRequired()]
    )

    location = StringField(
        label=_("Location"),
        validators=[InputRequired()]
    )

    spots = IntegerField(
        label=_("Spots"),
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
    def start(self):
        return replace_timezone(
            datetime(
                self.start_date.data.year,
                self.start_date.data.month,
                self.start_date.data.day,
                self.start_time.data.hour,
                self.start_time.data.minute
            ),
            self.timezone
        )

    @property
    def end(self):
        return replace_timezone(
            datetime(
                self.end_date.data.year,
                self.end_date.data.month,
                self.end_date.data.day,
                self.end_time.data.hour,
                self.end_time.data.minute
            ),
            self.timezone
        )

    def validate(self):
        result = super().validate()

        if self.start_date.data and self.end_date.data:
            if self.end_date.data > self.start_date.data:
                self.end_date.errors.append(
                    _("The end date must be later than the start date")
                )
                result = False

        if self.min_age.data and self.max_age.data:
            if self.min_age.data > self.max_age.data:
                self.min_age.errors.append(
                    _("The minium age cannot be higher than the maximum age")
                )
                result = False

        return result

    def process(self, *args, **kwargs):

        super().process(*args, **kwargs)

        model = kwargs.get('obj')

        if model:
            self.start_date.data = model.localized_start.date()
            self.start_time.data = model.localized_start.time()
            self.end_date.data = model.localized_end.date()
            self.end_time.data = model.localized_end.time()

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'start_date',
            'start_time',
            'end_date',
            'end_time'
        })

        model.timezone = self.timezone
        model.start = self.start
        model.end = self.end
        model.booking_start = utcnow()
