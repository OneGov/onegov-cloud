from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import StringField, TextAreaField
from wtforms.validators import InputRequired


class NotificationTemplateForm(Form):

    subject = StringField(
        label=_("Subject"),
        validators=[InputRequired()]
    )

    text = TextAreaField(
        label=_("Message"),
        validators=[InputRequired()],
        render_kw={'rows': 8}
    )


class NotificationTemplateSendForm(Form):
    pass
