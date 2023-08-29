from onegov.form import Form
from onegov.wtfs import _
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.wtfs.models import Notification


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

    def update_model(self, model: 'Notification') -> None:
        model.title = self.title.data
        model.text = self.text.data

    def apply_model(self, model: 'Notification') -> None:
        self.title.data = model.title
        self.text.data = model.text
