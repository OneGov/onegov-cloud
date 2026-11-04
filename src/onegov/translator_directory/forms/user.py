from onegov.org.forms import ManageUserForm
from onegov.translator_directory import _
from wtforms import SelectChoice


class ManageUserFormCustom(ManageUserForm):
    """ Defines the edit user form. """

    def on_request(self) -> None:
        super().on_request()
        self.role.choices = [
            SelectChoice('admin', _('Admin')),
            SelectChoice('editor', _('Editor')),
            SelectChoice('member', _('Member')),
            SelectChoice('translator', _('Translator'))
        ]
