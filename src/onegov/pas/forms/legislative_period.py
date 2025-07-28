from __future__ import annotations

from datetime import date
from onegov.form import Form
from onegov.pas import _
from wtforms.fields import StringField
from wtforms.fields import DateField
from wtforms.validators import InputRequired


class LegislativePeriodForm(Form):

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
