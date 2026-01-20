from __future__ import annotations

from onegov.org.forms import ManageUserForm
from onegov.translator_directory import _


class ManageUserFormCustom(ManageUserForm):
    """ Defines the edit user form. """

    def on_request(self) -> None:
        super().on_request()
        self.role.choices = [
            ('admin', _('Admin')),
            ('editor', _('Editor')),
            ('member', _('Member')),
            ('translator', _('Translator'))
        ]
