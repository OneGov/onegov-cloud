from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import HoneyPotField
from onegov.org import _
from wtforms.fields import EmailField, StringField
from wtforms.validators import InputRequired


class CitizenLoginForm(Form):

    email = EmailField(
        label=_('E-Mail'),
        validators=[InputRequired()]
    )

    duplicate_of = HoneyPotField(
        render_kw={
            'autocomplete': 'lazy-wolves'
        }
    )


class ConfirmCitizenLoginForm(Form):

    token = StringField(
        label=_('Token'),
        validators=[InputRequired()]
    )

    duplicate_of = HoneyPotField(
        render_kw={
            'autocomplete': 'lazy-wolves'
        }
    )
