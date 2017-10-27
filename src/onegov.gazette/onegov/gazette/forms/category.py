from onegov.form import Form
from onegov.gazette import _
from onegov.gazette.models import Category
from onegov.gazette.validators import UniqueColumnValue
from wtforms import BooleanField
from wtforms import HiddenField
from wtforms import StringField
from wtforms.validators import InputRequired


class CategoryForm(Form):

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
    )

    active = BooleanField(
        label=_("Active"),
        default=True
    )

    name = StringField(
        label=_("ID"),
        description=_("Leave blank to set the value automatically."),
        validators=[
            UniqueColumnValue(
                column=Category.name,
                old_field='name_old'
            )
        ]
    )

    name_old = HiddenField()

    def update_model(self, model):
        model.title = self.title.data
        model.active = self.active.data
        if self.name.data:
            model.name = self.name.data

    def apply_model(self, model):
        self.title.data = model.title
        self.active.data = model.active
        self.name.data = model.name
        self.name_old.data = model.name
