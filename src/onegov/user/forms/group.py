from onegov.form import Form
from onegov.user import _
from wtforms import StringField
from wtforms.validators import InputRequired


class UserGroupForm(Form):

    """ A generic user group form for onegov.user """

    name = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ]
    )

    def update_model(self, model):
        model.name = self.name.data

    def apply_model(self, model):
        self.name.data = model.name
