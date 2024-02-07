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
            ('Gemeindekanzlei/Einwohnerkontrolle',
             'Gemeindekanzlei/Einwohnerkontrolle'),
            ('Stabsstelle Gemeindeschreiber',
             'Stabsstelle Gemeindeschreiber'),
            ('Jugend /Sport/Vereine/Kultur',
             'Jugend /Sport/Vereine/Kultur'),
            ('Planung/Bau & Umwelt/Energie/Sicherheit',
             'Planung/Bau & Umwelt/Energie/Sicherheit'),
            ('Soziales/Gesundheit',
             'Soziales/Gesundheit')
        ]
    )

    confirmation = BooleanField(
        label=_("Confirmation"),
        description=_(
            "I confirm that I am aware that this chat will be saved and the "
            "history will be sent to me by email."),
        validators=[
            InputRequired()
        ],
    )


class ChatActionsForm(Form):

    chat_id = HiddenField(
        label=_("Chat ID"),
    )
