from onegov.form import Form
from onegov.wtfs import _
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import InputRequired


class NotificationForm(Form):

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
    )

    text = TextAreaField(
        label=_("Text"),
        validators=[
            InputRequired()
        ]
    )

    def update_model(self, model):
        model.title = self.title.data
        model.text = self.text.data

    def apply_model(self, model):
        self.title.data = model.title
        self.text.data = model.text
