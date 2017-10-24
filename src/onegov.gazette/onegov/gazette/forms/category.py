from onegov.form import Form
from onegov.gazette import _
from wtforms import BooleanField
from wtforms import StringField
from wtforms.validators import InputRequired


class CategoryForm(Form):

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
    )

    external = StringField(
        label=_("External")
    )
    active = BooleanField(
        label=_("Active"),
        default=True
    )

    def update_model(self, model):
        model.title = self.title.data
        model.external = self.external.data
        model.active = self.active.data

    def apply_model(self, model):
        self.title.data = model.title
        self.external.data = model.external
        self.active.data = model.active
