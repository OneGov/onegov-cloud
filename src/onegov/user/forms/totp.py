from __future__ import annotations

from onegov.form import Form
from onegov.user import _
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class TOTPForm(Form):

    totp = StringField(
        label=_('Code'),
        validators=[InputRequired()],
        render_kw={'autocomplete': 'one-time-code'}
    )
