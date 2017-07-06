from onegov.form import Form
from onegov.org import _
from wtforms import TextAreaField
from wtforms import validators


class TicketNoteForm(Form):
    """ Defines the form for pages with the 'page' trait. """

    text = TextAreaField(
        label=_("Text"),
        description=_("Your note about this ticket"),
        validators=[validators.InputRequired()],
        render_kw={'rows': 10})
