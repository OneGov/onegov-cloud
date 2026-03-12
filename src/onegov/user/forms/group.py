from __future__ import annotations

from onegov.form import Form
from onegov.user import _
from wtforms.fields import StringField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user import UserGroup


class UserGroupForm(Form):

    """ A generic user group form for onegov.user """

    name = StringField(
        label=_('Name'),
        validators=[
            InputRequired()
        ]
    )

    def update_model(self, model: UserGroup) -> None:
        model.name = self.name.data

    def apply_model(self, model: UserGroup) -> None:
        self.name.data = model.name
