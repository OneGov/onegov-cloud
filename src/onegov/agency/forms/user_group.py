from __future__ import annotations

from onegov.agency import _
from onegov.agency.collections import ExtendedAgencyCollection
from onegov.form.fields import ChosenSelectMultipleField
from onegov.user import RoleMapping
from onegov.org.forms import ManageUserGroupForm
from wtforms.fields import RadioField


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user import UserGroup


class UserGroupForm(ManageUserGroupForm):

    agencies = ChosenSelectMultipleField(
        label=_('Agencies'),
        choices=[]
    )

    immediate_notification = RadioField(
        label=_(
            'Immediate e-mail notification to members upon ticket submission'
        ),
        choices=(
            ('yes', _('Yes')),
            ('no', _('No'))
        ),
        default='no'
    )

    def on_request(self) -> None:
        super().on_request()
        self.agencies.choices = [
            (str(a.id), a.title)
            for a in ExtendedAgencyCollection(self.request.session).query()
        ]

    def update_model(self, model: UserGroup) -> None:
        super().update_model(model)
        model.role_mappings = [  # type:ignore[assignment]
            RoleMapping(
                group_id=model.id,
                content_type='agencies',
                content_id=agency,
                role='editor'
            ) for agency in self.agencies.data or ()
        ]
        # initialize meta field with empty dict
        if not model.meta:
            model.meta = {}
        model.meta['immediate_notification'] = self.immediate_notification.data

    def apply_model(self, model: UserGroup) -> None:
        super().apply_model(model)
        mappings = model.role_mappings.all()
        self.agencies.data = [m.content_id for m in mappings]
        if model.meta:
            self.immediate_notification.data = model.meta.get(
                'immediate_notification', 'no')
