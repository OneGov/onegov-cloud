from onegov.agency.collections import ExtendedAgencyCollection
from onegov.form import Form
from onegov.form.fields import ChosenSelectMultipleField
from onegov.user import _
from onegov.user import User
from onegov.user import UserCollection
from onegov.user import RoleMapping
from wtforms import StringField
from wtforms.validators import InputRequired


class UserGroupForm(Form):

    name = StringField(
        label=_('Name'),
        validators=[
            InputRequired()
        ]
    )

    users = ChosenSelectMultipleField(
        label=_('Users'),
        choices=[]
    )

    agencies = ChosenSelectMultipleField(
        label=_('Agencies'),
        choices=[]
    )

    def on_request(self):
        self.users.choices = [
            (str(u.id), u.title)
            for u in UserCollection(self.request.session).query()
        ]
        self.agencies.choices = [
            (str(a.id), a.title)
            for a in ExtendedAgencyCollection(self.request.session).query()
        ]

    def update_model(self, model):
        model.name = self.name.data
        model.users = UserCollection(self.request.session).query().filter(
            User.id.in_(self.users.data)
        ).all()
        model.role_mappings = [
            RoleMapping(
                group_id=model.id,
                content_type='agencies',
                content_id=agency,
                role='editor'
            ) for agency in self.agencies.data
        ]

    def apply_model(self, model):
        mappings = model.role_mappings.all()
        self.name.data = model.name
        self.users.data = [str(u.id) for u in self.model.users]
        self.agencies.data = [m.content_id for m in mappings]
