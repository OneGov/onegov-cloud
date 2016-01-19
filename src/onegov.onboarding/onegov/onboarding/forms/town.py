from onegov.form import Form
from onegov.onboarding import _
from wtforms import StringField, validators
from wtforms.fields.html5 import EmailField
from wtforms_components import ColorField


class TownForm(Form):
    """ First step when starting a new town. """

    name = StringField(
        label=_("Town Name"),
        description=_("The name of your town (real or fictitious)"),
        validators=[validators.InputRequired()],
        render_kw={'autofocus': ''}
    )

    user = EmailField(
        label=_("E-Mail"),
        description=_("Your e-mail address"),
        validators=[validators.InputRequired(), validators.Email()]
    )

    color = ColorField(
        label=_("Primary Color"),
        validators=[validators.InputRequired()]
    )


class FinishForm(Form):
    pass
