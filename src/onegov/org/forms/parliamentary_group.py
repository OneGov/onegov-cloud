from __future__ import annotations

from onegov.form import Form
from onegov.org.forms.fields import HtmlField
from onegov.org import _
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class ParliamentaryGroupForm(Form):

    name = StringField(
        label=_('Name'),
        validators=[InputRequired()],
    )

    start = DateField(
        label=_('Start'),
        validators=[Optional()],
    )

    end = DateField(
        label=_('End'),
        validators=[Optional()],
    )

    description = HtmlField(
        label=_('Description')
    )
