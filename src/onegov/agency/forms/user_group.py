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
        user_ids = {str(r.id) for r in model.users.with_entities(User.id)}
        user_ids |= set(self.users.data)
        users = UserCollection(self.request.session).query()
        users = users.filter(User.id.in_(user_ids)).all()
        for user in users:
            if user != self.request.current_user:
                user.logout_all_sessions(self.request)

        users = UserCollection(self.request.session).query()
        users = users.filter(User.id.in_(self.users.data)).all()
        model.name = self.name.data
        model.users = users
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
        self.users.data = [str(u.id) for u in model.users]
        self.agencies.data = [m.content_id for m in mappings]
