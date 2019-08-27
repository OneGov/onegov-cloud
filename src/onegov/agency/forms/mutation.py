from onegov.agency import _
from onegov.form import Form
from wtforms import validators
from wtforms import TextAreaField
from wtforms.fields.html5 import EmailField


class MutationForm(Form):
    """ Form to report a mutation of an organization. """

    email = EmailField(
        label=_("E-Mail"),
        description="max.muster@example.org",
        validators=[validators.InputRequired(), validators.Email()]
    )

    message = TextAreaField(
        label=_("Message"),
        render_kw={'rows': 12},
        validators=[validators.InputRequired()]
    )
