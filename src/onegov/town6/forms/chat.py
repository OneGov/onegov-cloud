from __future__ import annotations

from wtforms.fields import EmailField, HiddenField, SelectField, StringField
from wtforms.fields import BooleanField
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.town6 import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.request import TownRequest


class ChatInitiationForm(Form):

    request: TownRequest

    name = StringField(
        label=_('Name'),
        validators=[
            InputRequired()
        ],
    )

    email = EmailField(
        label=_('E-mail'),
        validators=[
            InputRequired()
        ],
    )

    topic = SelectField(
        label=_('Topic'),
        choices=[]
    )

    confirmation = BooleanField(
        label=_('Confirmation'),
        description=_(
            'I confirm that I am aware that this chat will be saved and the '
            'history will be sent to me by email.'),
        validators=[
            InputRequired()
        ],
    )

    def populate_topics(self) -> None:
        topics = self.request.app.org.chat_topics
        if topics:
            self.topic.choices = [(t, t) for t in topics]
            general = self.request.translate(_('General'))
            self.topic.choices.append((general, general))
        else:
            self.delete_field('topic')

    def on_request(self) -> None:
        self.populate_topics()


class ChatActionsForm(Form):

    chat_id = HiddenField(
        label=_('Chat ID'),
    )
