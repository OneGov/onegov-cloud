from __future__ import annotations

from onegov.form import Form
from onegov.user import _
from wtforms.fields import IntegerField
from wtforms.fields import RadioField
from wtforms.validators import InputRequired
from wtforms.validators import NumberRange


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user import Auth


class SignupLinkForm(Form):
    """ A form to generate signup links for specific roles. """

    role = RadioField(
        label=_('Role'),
        validators=[InputRequired()],
        choices=[
            ('member', ('Member')),
            ('editor', _('Editor')),
            ('admin', _('Admin'))
        ]
    )

    max_age = RadioField(
        label=_('Expires in'),
        validators=[InputRequired()],
        choices=[
            ('hour', _('1 hour')),
            ('day', _('24 hours')),
            ('week', _('7 days')),
            ('month', _('30 days'))
        ]
    )

    max_uses = IntegerField(
        label=_('Number of Signups'),
        validators=[
            InputRequired(),
            NumberRange(1, 10000)
        ],
    )

    def signup_token(self, auth: Auth) -> str:
        assert self.role.data in ('member', 'editor', 'admin')

        max_age = {
            'hour': 60 * 60,
            'day': 60 * 60 * 24,
            'week': 60 * 60 * 24 * 7,
            'month': 60 * 60 * 24 * 30
        }.get(self.max_age.data, 60 * 60)

        assert self.max_uses.data is not None
        max_uses = int(self.max_uses.data)

        return auth.new_signup_token(self.role.data, max_age, max_uses)
