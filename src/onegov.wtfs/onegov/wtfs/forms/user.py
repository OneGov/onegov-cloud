from onegov.core.crypto import random_password
from onegov.core.orm.func import unaccent
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.validators import InputRequiredIf
from onegov.form.validators import UniqueColumnValue
from onegov.user import User
from onegov.wtfs import _
from onegov.wtfs.models import Municipality
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
        depends_on=('role', '!admin'),
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
            ('admin', _("Admin")),
            ('editor', _("Editor")),
            ('member', _("Member"))
        ],
        default='member',
        validators=[
            InputRequired()
        ]
    )

    municipality_id = ChosenSelectField(
        label=_("Municipality"),
        choices=[],
        validators=[
            InputRequiredIf('role', 'editor')
        ],
        depends_on=('role', '!admin'),
    )

    def on_request(self):
        query = self.request.session.query(
            Municipality.id.label('id'),
            Municipality.name.label('name'),
            Municipality.meta['bfs_number'].label('bfs_number')
        )
        query = query.order_by(unaccent(Municipality.name))
        self.municipality_id.choices = [
            (r.id.hex, f"{r.name} ({r.bfs_number})") for r in query
        ]
        self.municipality_id.choices.insert(
            0, ('', self.request.translate(_("- none -")))
        )

    def update_model(self, model):
        super().update_model(model)
        model.role = self.role.data
        model.group_id = self.municipality_id.data or None

    def apply_model(self, model):
        super().apply_model(model)
        self.role.data = model.role
        self.municipality_id.data = (
            model.group_id.hex if model.group_id else ''
        )
