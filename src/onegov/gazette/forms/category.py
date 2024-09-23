from onegov.form import Form
from onegov.form.validators import UniqueColumnValue
from onegov.gazette import _
from onegov.gazette.models import Category
from onegov.gazette.models import GazetteNotice
from onegov.gazette.validators import UnusedColumnKeyValue
from wtforms.fields import BooleanField
from wtforms.fields import StringField
from wtforms.validators import InputRequired


class CategoryForm(Form):

    title = StringField(
        label=_('Title'),
        validators=[
            InputRequired()
        ]
    )

    active = BooleanField(
        label=_('Active'),
        default=True
    )

    name = StringField(
        label=_('ID'),
        description=_('Leave blank to set the value automatically.'),
        validators=[
            UniqueColumnValue(Category),
            UnusedColumnKeyValue(GazetteNotice._categories)
        ]
    )

    def update_model(self, model: Category) -> None:
        assert self.title.data is not None
        model.title = self.title.data
        model.active = self.active.data
        if self.name.data:
            model.name = self.name.data

    def apply_model(self, model: Category) -> None:
        self.title.data = model.title
        if model.active is not None:
            self.active.data = model.active
        self.name.data = model.name
        self.name.default = model.name
        if model.in_use:
            self.name.render_kw = {'readonly': True}
