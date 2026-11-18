from onegov.form import merge_forms
from onegov.org.forms import ManageUserForm
from onegov.org.forms.user import PartialNewUserForm
from onegov.pas import _
from wtforms import SelectChoice


from typing import TYPE_CHECKING


class ManageUserFormCustom(ManageUserForm):
    def on_request(self) -> None:
        super().on_request()
        self.role.choices = [
            SelectChoice('admin', _('Admin')),
            SelectChoice('parliamentarian', _('Parliamentarian')),
            SelectChoice('commission_president', _('Commission President'))
        ]


# The problem is that NewUserFormCustom is a runtime-created form
# class from merge_forms(), which mypy can't properly type check.
if TYPE_CHECKING:
    class NewUserFormCustom(PartialNewUserForm, ManageUserFormCustom):
        pass
else:
    NewUserFormCustom = merge_forms(PartialNewUserForm, ManageUserFormCustom)
