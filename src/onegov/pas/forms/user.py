from __future__ import annotations
from onegov.org.forms import ManageUserForm
from onegov.pas import _


class ManageUserFormCustom(ManageUserForm):
    """ Defines the edit user form for PAS. """

    def on_request(self) -> None:
        super().on_request()
        self.role.choices = [
            ('admin', _('Admin')),
            ('editor', _('Editor')),
            ('member', _('Member')),
            ('parliamentarian', _('Parliamentarian'))
        ]
