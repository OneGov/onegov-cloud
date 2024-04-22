from datetime import date
from onegov.form import Form
from onegov.pas import _
from onegov.pas.models import CostOfLivingAdjustment
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


def default_year() -> int:
    return date.today().year


class CostOfLivingAdjustmentForm(Form):

    year = IntegerField(
        label=_('Year'),
        validators=[InputRequired()],
        default=default_year
    )

    percentage = DecimalField(
        label=_('Percentage'),
        validators=[InputRequired()]
    )

    def validate_year(self, field: IntegerField) -> None:
        if field.data is not None:
            query = self.request.session.query(CostOfLivingAdjustment)
            query = query.filter_by(year=field.data)
            if query.first():
                raise ValidationError(_(
                    'Cost of living adjustment for ${year} alredy exists',
                    mapping={'year': field.data}
                ))
