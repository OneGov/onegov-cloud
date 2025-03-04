from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.form.fields import PhoneNumberField
from onegov.form.validators import UniqueColumnValue
from onegov.gazette import _
from onegov.user import User, UserGroupCollection
from onegov.user import UserGroup
from sqlalchemy import cast
from sqlalchemy import String
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import Email
from wtforms.validators import InputRequired


class UserForm(Form):

    role = RadioField(
        label=_('Role'),
        choices=[],
        default='member',
        validators=[
            InputRequired()
        ]
    )

    group_ids = ChosenSelectMultipleField(
        label=_('Group'),
        choices=[]
    )

    name = StringField(
        label=_('Name'),
        validators=[
            InputRequired()
        ]
    )

    username = StringField(
        label=_('E-Mail'),
        validators=[
            InputRequired(),
            Email(),
            UniqueColumnValue(User)
        ]
    )

    phone_number = PhoneNumberField(
        label=_('Phone number'),
        description='+41791112233',
    )

    def on_request(self) -> None:
        self.role.choices = []
        model = getattr(self, 'model', None)
        if self.request.is_private(model):
            self.role.choices = [('member', _('Editor'))]
        if self.request.is_secret(model):
            self.role.choices.append(('editor', _('Publisher')))

        self.group_ids.choices = self.request.session.query(
            cast(UserGroup.id, String), UserGroup.name
        ).all()

    def update_model(self, model: User) -> None:
        assert self.username.data is not None
        model.username = self.username.data
        model.role = self.role.data
        model.realname = self.name.data
        if self.group_ids.data:
            model.groups = (
                UserGroupCollection(self.request.session)
                .query()
                .filter(UserGroup.id.in_(self.group_ids.data))
                .all()
            )
        else:
            model.groups = []
        model.phone_number = self.phone_number.formatted_data

    def apply_model(self, model: User) -> None:
        self.username.data = model.username
        self.role.data = model.role
        self.name.data = model.realname
        self.group_ids.data = [str(group.id) for group in model.groups]
        self.phone_number.data = model.phone_number


class ExportUsersForm(Form):

    group_names = ChosenSelectMultipleField(
        label=_('Group Names'),
        choices=[]
    )

    def populate_group_names(self) -> None:
        groups = UserGroupCollection(self.request.session)
        cls = groups.model_class
        q = groups.query().with_entities(cls.id, cls.name)
        self.group_names.choices = [
            (str(entry.id), entry.name) for entry in q
        ]

    def on_request(self) -> None:
        self.populate_group_names()
