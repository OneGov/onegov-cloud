from onegov.form import Form
from onegov.gazette import _
from onegov.gazette.fields import SelectField
from onegov.gazette.validators import UniqueColumnValue
from onegov.user import User
from onegov.user import UserGroup
from sqlalchemy import cast
from sqlalchemy import String
from wtforms import RadioField
from wtforms import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


class UserForm(Form):

    role = RadioField(
        label=_("Role"),
        choices=[
            ('editor', _("Publisher")),
            ('member', _("Editor"))
        ],
        default='member',
        validators=[
            InputRequired()
        ]
    )

    group = SelectField(
        label=_("Group"),
        choices=[('', '')]
    )

    name = StringField(
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

    def on_request(self):
        session = self.request.session
        self.group.choices = session.query(
            cast(UserGroup.id, String), UserGroup.name
        ).all()
        self.group.choices.insert(
            0, ('', self.request.translate(_("- none -")))
        )

    def update_model(self, model):
        model.username = self.username.data
        model.role = self.role.data
        model.realname = self.name.data
        model.group_id = self.group.data or None

    def apply_model(self, model):
        self.username.data = model.username
        self.role.data = model.role
        self.name.data = model.realname
        self.group.data = str(model.group_id or '')
