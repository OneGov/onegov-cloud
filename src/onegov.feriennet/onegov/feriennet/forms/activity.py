from onegov.feriennet import _
from onegov.core.utils import sanitize_html
from onegov.form import Form
from onegov.org.utils import annotate_html
from wtforms import TextField, TextAreaField
from wtforms.validators import InputRequired


class VacationActivityForm(Form):

    title = TextField(
        label=_("Title"),
        description=_("The title of the activity"),
        validators=[InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes briefly what this activity is about"),
        validators=[InputRequired()],
        render_kw={'rows': 4})

    text = TextAreaField(
        label=_("Text"),
        render_kw={'class_': 'editor'},
        filters=[sanitize_html, annotate_html])
