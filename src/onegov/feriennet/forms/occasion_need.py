from __future__ import annotations

from onegov.activity import OccasionNeed
from onegov.activity.types import BoundedIntegerRange
from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import BooleanField
from wtforms.fields import IntegerField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired, NumberRange, ValidationError


class OccasionNeedForm(Form):

    name = StringField(
        label=_('Name'),
        description=_('Chaperones, Cars, Meals'),
        validators=[InputRequired()]
    )

    description = TextAreaField(
        label=_('Description'),
        render_kw={'rows': 6}
    )

    min_number = IntegerField(
        label=_('Need at least'),
        validators=[
            InputRequired(),
            NumberRange(0, 10000)
        ]
    )

    max_number = IntegerField(
        label=_('Need up to'),
        validators=[
            InputRequired(),
            NumberRange(0, 10000)
        ]
    )

    accept_signups = BooleanField(
        label=_('Accept signups by volunteers'),
        description=_(
            'Only relevant if the experimental volunteer feature is used'
        )
    )

    @property
    def number(self) -> BoundedIntegerRange:
        lower = self.min_number.data or 0
        upper = self.max_number.data or 0

        return BoundedIntegerRange(lower, upper + 1, bounds='[)')

    @number.setter
    def number(self, value: BoundedIntegerRange) -> None:
        if value:
            lower, upper = value.lower, value.upper
        else:
            lower, upper = 0, 1

        self.min_number.data = lower
        self.max_number.data = upper - 1

    def ensure_valid_range(self) -> bool | None:
        lower = self.min_number.data or 0
        upper = self.max_number.data or 0

        if lower > upper:
            assert isinstance(self.min_number.errors, list)
            self.min_number.errors.append(_(
                'Minimum is larger than maximum'
            ))
            return False
        return True

    def validate_name(self, field: StringField) -> None:
        occasion_id = getattr(self.model, 'occasion_id', None) or self.model.id

        exists = (
            self.request.session.query(OccasionNeed)
            .filter_by(name=self.name.data)
            .filter_by(occasion_id=occasion_id)
            .filter(OccasionNeed.id != self.model.id)
            .exists()
        )

        if self.request.session.query(exists).scalar():
            raise ValidationError(
                _('This name has already been used for this occasion')
            )

    def populate_obj(self, model: OccasionNeed) -> None:  # type:ignore
        super().populate_obj(model, exclude={
            'number',
        })

        model.number = self.number

    def process_obj(self, model: OccasionNeed) -> None:  # type:ignore
        super().process_obj(model)

        self.number = model.number
