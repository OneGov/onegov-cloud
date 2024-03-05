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
        choices=[]
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

    def populate_topics(self):
        topics = self.request.app.org.chat_topics
        if topics:
            for t in topics:
                self.topic.choices.append((t, t))
            self.topic.choices.append((self.request.translate(_('General')),
                                       self.request.translate(_('General'))))
        else:
            self.delete_field('topic')

    def on_request(self):
        self.populate_topics()


class ChatActionsForm(Form):

    chat_id = HiddenField(
        label=_("Chat ID"),
    )
