from onegov.form import Form, merge_forms
from onegov.org import _
from onegov.user import UserCollection, is_valid_yubikey_format
from wtforms import BooleanField, RadioField, TextField, validators
from wtforms.fields.html5 import EmailField


AVAILABLE_ROLES = [
    ('admin', _("Admin")),
    ('editor', _("Editor")),
    ('member', _("Member"))
]


class ManageUserForm(Form):
    """ Defines the edit user form. """

    role = RadioField(
        label=_("Role"),
        choices=AVAILABLE_ROLES,
        default='member'
    )

    active = BooleanField(_("Active"), default=True)

    yubikey = TextField(
        label=_("Yubikey"),
        description=_("Plug your YubiKey into a USB slot and press it."),
        render_kw={'autocomplete': 'off'}
    )

    def validate_yubikey(self, field):
        if not self.active.data:
            return

        if not field.data:
            if not self.request.app.settings.org.enable_yubikey:
                return

            if self.role.data in ('admin', 'editor'):
                raise validators.ValidationError(_(
                    "Administrators and editors must use a Yubikey"
                ))
            else:
                return

        if not is_valid_yubikey_format(field.data):
            raise validators.ValidationError(_("Invalid Yubikey"))

        users = UserCollection(self.request.app.session())
        user = users.by_yubikey(field.data)

        if not hasattr(self, 'current_username'):
            raise NotImplementedError()

        if user and user.username != self.current_username:
            raise validators.ValidationError(
                _("This Yubikey is already used by ${username}", mapping={
                    'username': user.username
                })
            )


class PartialNewUserForm(Form):
    """ Defines parts of the new user form not found in the manage user form.

    """

    username = EmailField(
        label=_("E-Mail"),
        description=_("The users e-mail address (a.k.a. username)"),
        validators=[validators.InputRequired(), validators.Email()]
    )

    @property
    def current_username(self):
        return self.username.data

    def validate_username(self, field):
        users = UserCollection(self.request.app.session())

        if users.by_username(field.data):
            raise validators.ValidationError(
                _("A user with this e-mail address exists already"))


NewUserForm = merge_forms(PartialNewUserForm, ManageUserForm)
