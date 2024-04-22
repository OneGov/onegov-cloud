from datetime import date
from onegov.form import Form
from onegov.pas import _
from wtforms.fields import DecimalField
from wtforms.fields import IntegerField
from wtforms.validators import InputRequired


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
