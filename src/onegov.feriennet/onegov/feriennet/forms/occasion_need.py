from onegov.activity import OccasionNeed
from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import StringField, TextAreaField
from wtforms.fields.html5 import IntegerField
from wtforms.validators import InputRequired, NumberRange
from psycopg2.extras import NumericRange


class OccasionNeedForm(Form):

    name = StringField(
        label=_("Name"),
        description=_("Chaperones, Cars, Meals"),
        validators=[InputRequired()]
    )

    description = TextAreaField(
        label=_("Description"),
        render_kw={'rows': 6}
    )

    min_number = IntegerField(
        label=_("Need at least"),
        validators=[
            InputRequired(),
            NumberRange(0, 10000)
        ]
    )

    max_number = IntegerField(
        label=_("Need up to"),
        validators=[
            InputRequired(),
            NumberRange(0, 10000)
        ]
    )

    @property
    def number(self):
        lower = self.min_number.data or 0
        upper = self.max_number.data or 0

        return NumericRange(lower, upper + 1, bounds='[)')

    @number.setter
    def number(self, value):
        if value:
            lower, upper = value.lower, value.upper
        else:
            lower, upper = 0, 1

        self.min_number.data = lower
        self.max_number.data = upper - 1

    def ensure_valid_range(self):
        lower = self.min_number.data or 0
        upper = self.max_number.data or 0

        if lower > upper:
            self.min_number.errors.append(_(
                "Minimum is larger than maximum"
            ))
            return False

    def ensure_unique_name(self):
        occasion_id = getattr(self.model, 'occasion_id', None) or self.model.id

        exists = self.request.session.query(OccasionNeed)\
            .filter_by(name=self.name.data)\
            .filter_by(occasion_id=occasion_id)\
            .filter(OccasionNeed.id != self.model.id)\
            .first()

        if exists:
            self.name.errors.append(
                _("This name has already been used for this occasion")
            )
            return False

    def populate_obj(self, model):
        super().populate_obj(model, exclude={
            'number',
        })

        model.number = self.number

    def process_obj(self, model):
        super().process_obj(model)

        self.number = model.number
