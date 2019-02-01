from onegov.core.crypto import random_password
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.validators import InputRequiredIf
from onegov.form.validators import UniqueColumnValue
from onegov.user import User
from onegov.user import UserGroup
from onegov.wtfs import _
from sqlalchemy import cast
from sqlalchemy import String
from wtforms import BooleanField
from wtforms import RadioField
from wtforms import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


class UserForm(Form):

    realname = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ]
    )

    username = StringField(
        label=_("E-Mail"),
        validators=[
            InputRequired(),
            Email(),
            UniqueColumnValue(User)
        ]
    )

    contact = BooleanField(
        label=_("Contact"),
    )

    def update_model(self, model):
        model.realname = self.realname.data
        model.username = self.username.data
        model.data = model.data or {}
        model.data['contact'] = self.contact.data or False
        model.role = 'member'
        model.group_id = self.request.identity.groupid

        # set some initial values if we create this user
        if not model.password:
            model.password = model.password or random_password(16)
        if not model.modified:
            model.modified = model.timestamp()

        model.logout_all_sessions(self.request)

    def apply_model(self, model):
        self.realname.data = model.realname
        self.username.data = model.username
        self.contact.data = (model.data or {}).get('contact', False)


class UnrestrictedUserForm(UserForm):

    role = RadioField(
        label=_("Role"),
        choices=[
            ('editor', _("Editor")),
            ('member', _("Member"))
        ],
        default='member',
        validators=[
            InputRequired()
        ]
    )

    group_id = ChosenSelectField(
        label=_("User group"),
        choices=[],
        validators=[
            InputRequiredIf('role', 'editor')
        ]
    )

    def on_request(self):
        self.group_id.choices = self.request.session.query(
            cast(UserGroup.id, String), UserGroup.name
        ).all()
        self.group_id.choices.insert(
            0, ('', self.request.translate(_("- none -")))
        )

    def update_model(self, model):
        super().update_model(model)
        model.role = self.role.data
        model.group_id = self.group_id.data or None

    def apply_model(self, model):
        super().apply_model(model)
        self.role.data = model.role
        self.group_id.data = str(model.group_id or '')
