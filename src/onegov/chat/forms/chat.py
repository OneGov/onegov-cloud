from wtforms.fields import EmailField, HiddenField, SelectField, StringField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.org import _


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
        choices=[
            ('a', 'a'),
            ('b', 'b'),
            ('v', 'v')
        ]
    )


class ChatActionsForm(Form):

    chat_id = HiddenField(
        label=_("Chat ID"),
    )
