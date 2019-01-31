from onegov.form import Form
from onegov.wtfs import _
from wtforms import StringField
from wtforms.validators import InputRequired


class UserGroupForm(Form):

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
