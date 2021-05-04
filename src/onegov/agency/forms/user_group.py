from onegov.agency.collections import ExtendedAgencyCollection
from onegov.form.fields import ChosenSelectMultipleField
from onegov.user import _
from onegov.user import RoleMapping
from onegov.org.forms import ManageUserGroupForm


class UserGroupForm(ManageUserGroupForm):

    agencies = ChosenSelectMultipleField(
        label=_('Agencies'),
        choices=[]
    )

    def on_request(self):
        super().on_request()
        self.agencies.choices = [
            (str(a.id), a.title)
            for a in ExtendedAgencyCollection(self.request.session).query()
        ]

    def update_model(self, model):
        super().update_model(model)
        model.role_mappings = [
            RoleMapping(
                group_id=model.id,
                content_type='agencies',
                content_id=agency,
                role='editor'
            ) for agency in self.agencies.data
        ]

    def apply_model(self, model):
        super().apply_model(model)
        mappings = model.role_mappings.all()
        self.agencies.data = [m.content_id for m in mappings]
