from wtforms import StringField
from wtforms.validators import InputRequired

from onegov.core.utils import linkify
from onegov.form import Form
from onegov.form.fields import HtmlField
from onegov.fsi import _


class CourseForm(Form):

    # Course info
    name = StringField(
        label=_('Short Description'),
        validators=[
            InputRequired()
        ]
    )

    description = HtmlField(
        label=_('Description'),
        description=_('Enter all information to the course here'),
        validators=[
            InputRequired()
        ],
        render_kw={'rows': 10}
    )

    def get_useful_data(self, exclude={'csrf_token'}):
        result = super().get_useful_data(exclude)
        if self.description.data:
            result['description'] = linkify(
                self.description.data, escape=False)
        return result

    def apply_model(self, model):
        self.name.data = model.name
        self.description.data = model.description

    def update_model(self, model):
        model.name = self.name.data
        model.description = linkify(self.description.data, escape=False)
