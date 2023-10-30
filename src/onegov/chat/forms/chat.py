from onegov.form import Form
from onegov.org import _
from wtforms.fields import TextAreaField


class ChatForm(Form):

    message = TextAreaField(
        label=_("Message"),
        render_kw={'rows': 5}
    )
