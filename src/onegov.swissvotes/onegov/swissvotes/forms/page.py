from onegov.form import Form
from onegov.quill import QuillField
from onegov.swissvotes import _
from wtforms import StringField
from wtforms.validators import InputRequired


class PageForm(Form):

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
    )

    content = QuillField(
        label=_("Content"),
        tags=('strong', 'em', 'a', 'h3', 'ol', 'ul', 'blockquote'),
        validators=[
            InputRequired()
        ]
    )

    def update_model(self, model):
        model.title = self.title.data
        model.content = self.content.data

    def apply_model(self, model):
        self.title.data = model.title
        self.content.data = model.content
