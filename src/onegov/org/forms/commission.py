from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import TranslatedSelectField
from onegov.org.forms.fields import HtmlField
from onegov.org import _
from onegov.parliament.models.commission import TYPES
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class CommissionForm(Form):

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

    type = TranslatedSelectField(
        label=_('Type'),
        choices=list(TYPES.items()),
        validators=[InputRequired()],
        default='normal'
    )

    description = HtmlField(
        label=_('Description'),
    )
