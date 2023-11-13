from onegov.form import Form
from onegov.org import _
from wtforms.fields import StringField, EmailField, SelectField, HiddenField
from wtforms.validators import InputRequired


class ChatInitiationForm(Form):

    name = StringField(
        label=_("Name"),
        validators=[
            InputRequired()
        ],
    )

    email = EmailField(
        label=_("E-mail"),
        validators=[
            InputRequired()
        ],
    )

    topic = SelectField(
        label=_("Topic"),
        choices=['a', 'b', 'v']
    )


class ChatActionsForm(Form):

    chat_id = HiddenField(
        label=_("Chat ID"),
    )
