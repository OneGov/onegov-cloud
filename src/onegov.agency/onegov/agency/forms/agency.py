from onegov.agency import _
from onegov.form import Form
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import validators


class ExtendedAgencyForm(Form):
    """ Form to edit agencies. """

    # Public
    title = StringField(
        label=_("Title"),
        validators=[
            validators.InputRequired()
        ],
    )
    description = StringField(
        label=_("Description"),
    )
    address = TextAreaField(
        label=_("Portrait"),
        render_kw={'rows': 5}
    )
    # organigram
