from wtforms.fields import EmailField, HiddenField, SelectField, StringField
from wtforms.fields import BooleanField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.town6 import _


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
            ('Allgemein', 'Allgemein'),
            ('Steuern', 'Steuern'),
            ('Baugesuche', 'Baugesuche')
        ]
    )

    confirmation = BooleanField(
        label=_("Confirmation"),
        description=_(
            "Ich bestätige, dass mir bewusst ist, dass dieser Chat "
            "gespeichert und der Verlauf an mich per Mail gesendet wird."),
        validators=[
            InputRequired()
        ],
    )


class ChatActionsForm(Form):

    chat_id = HiddenField(
        label=_("Chat ID"),
    )
