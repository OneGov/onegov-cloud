from onegov.activity import OccasionCollection
from onegov.feriennet import _
from onegov.form import Form
from sedate import replace_timezone
from wtforms.fields import StringField, TextAreaField
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

        if self.min_spots.data and self.max_spots.data:
            if self.min_spots.data > self.max_spots.data:
                self.min_spots.errors.append(
                    _(
                        "The minium number of participants cannot be higher "
                        "than the maximum number of participants"
                    )
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
