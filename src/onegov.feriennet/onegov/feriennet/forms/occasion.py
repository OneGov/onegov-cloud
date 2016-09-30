from onegov.feriennet import _
from onegov.form import Form
from sedate import replace_timezone, utcnow
from wtforms.fields import StringField
from wtforms.fields.html5 import DateTimeField, IntegerField
from wtforms.validators import InputRequired, NumberRange


class OccasionForm(Form):

    timezone = 'Europe/Zurich'

    start = DateTimeField(
        label=_("Start"),
        validators=[InputRequired()]
    )

    end = DateTimeField(
        label=_("End"),
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
    def localized_start(self):
        return replace_timezone(
            self.start,
            self.timezone
        )

    @property
    def localized_end(self):
        return replace_timezone(
            self.end,
            self.timezone
        )

    def validate(self):
        result = super().validate()

        if self.start.data and self.end.data:
            if self.start.data > self.end.data:
                self.end.errors.append(
                    _("The end date must be after the start date")
                )
                result = False

        if self.min_age.data and self.max_age.data:
            if self.min_age.data > self.max_age.data:
                self.min_age.errors.append(
                    _("The minium age cannot be higher than the maximum age")
                )
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
        model.booking_start = utcnow()
