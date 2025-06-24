from __future__ import annotations

from wtforms import DateTimeField

from onegov.form import Form
from onegov.org.forms.fields import HtmlField
from onegov.pas import _
from wtforms.fields import DateField
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import Optional


class MeetingForm(Form):

    start_datetime = DateTimeField(
        label=_('Start'),
        validators=[Optional()],
    )

    address = HtmlField(
        label=_('Portrait'),
    )

    description = HtmlField(
        label=_('Description'),
    )
