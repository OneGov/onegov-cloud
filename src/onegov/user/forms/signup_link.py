from onegov.form import Form
from onegov.user import _
from wtforms import RadioField, validators
from wtforms.fields.html5 import IntegerField


class SignupLinkForm(Form):
    """ A form to generate signup links for specific roles. """

    role = RadioField(
        label=_("Role"),
        validators=[validators.InputRequired()],
        choices=[
            ('member', ("Member")),
            ('editor', _("Editor")),
            ('admin', _("Admin"))
        ]
    )

    max_age = RadioField(
        label=_("Expires in"),
        validators=[validators.InputRequired()],
        choices=[
            ('hour', _("1 hour")),
            ('day', _("24 hours")),
            ('week', _("7 days")),
            ('month', _("30 days"))
        ]
    )

    max_uses = IntegerField(
        label=_("Number of Signups"),
        validators=[
            validators.InputRequired(),
            validators.NumberRange(1, 10000)
        ],
    )

    def signup_token(self, auth):
        assert self.role.data in ('member', 'editor', 'admin')

        max_age = {
            'hour': 60 * 60,
            'day': 60 * 60 * 24,
            'week': 60 * 60 * 24 * 7,
            'month': 60 * 60 * 24 * 30
        }.get(self.max_age.data, 60 * 60)

        max_uses = int(self.max_uses.data)

        return auth.new_signup_token(self.role.data, max_age, max_uses)
