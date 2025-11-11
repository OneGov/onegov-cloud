from __future__ import annotations

from onegov.form import Form
from onegov.form.validators import ValidPassword
from onegov.user import _
from onegov.user import UserCollection
from onegov.user.collections import MIN_PASSWORD_LENGTH
from wtforms.fields import HiddenField
from wtforms.fields import PasswordField
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest


class RequestPasswordResetForm(Form):
    """ A generic password reset request form for onegov.user. """

    email = StringField(
        label=_('E-Mail Address'),
        validators=[InputRequired(), Email()],
        render_kw={'autofocus': True}
    )


class PasswordResetForm(Form):
    """ A generic password reset form for onegov.user. """

    email = StringField(
        label=_('E-Mail Address'),
        validators=[InputRequired(), Email()],
        render_kw={'autofocus': True}
    )
    password = PasswordField(
        label=_('New Password'),
        validators=[
            InputRequired(),
            ValidPassword(MIN_PASSWORD_LENGTH, _(
                'The password must be at least ten characters long'
            ))
        ],
        render_kw={'autocomplete': 'new-password'}
    )
    token = HiddenField()

    def update_password(self, request: CoreRequest) -> bool:
        """ Updates the password using the form data (if permitted to do so).

        Returns True if successful, False if not successful.
        """
        data = request.load_url_safe_token(
            self.token.data or '',
            max_age=86400
        )

        if not data or not data.get('username') or 'modified' not in data:
            return False

        # this should be true if the form has been validated
        assert self.email.data is not None
        assert self.password.data is not None
        if data['username'].lower() != self.email.data.lower():
            return False

        users = UserCollection(request.session)
        user = users.by_username(self.email.data)

        if not user:
            return False

        modified = user.modified.isoformat() if user.modified else ''
        if modified != data['modified']:
            return False

        user.password = self.password.data

        return True
