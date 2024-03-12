from datetime import date
from onegov.form.forms import NamedFileForm
from onegov.pas import _
from wtforms.fields import StringField
from wtforms.fields import DateField
from wtforms.validators import InputRequired


class LegislativePeriodForm(NamedFileForm):

    name = StringField(
        label=_('Name'),
        validators=[InputRequired()],
    )

    start = DateField(
        label=_('Start'),
        validators=[InputRequired()],
        default=date.today
    )

    end = DateField(
        label=_('End'),
        validators=[InputRequired()],
        default=date.today
    )
