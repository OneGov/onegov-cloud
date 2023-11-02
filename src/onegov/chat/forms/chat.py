from onegov.form import Form
from onegov.org import _
from wtforms.fields import StringField, EmailField, SelectField


class ChatInitiationForm(Form):

    name = StringField(
        label=_("Name"),
    )

    email = EmailField(
        label=_("E-mail"),
    )

    topic = SelectField(
        label=_("Topic"),
        choices=['a', 'b', 'v']
    )
