from onegov.form import Form
from onegov.form.filters import strip_whitespace
from onegov.org import _
from wtforms import TextAreaField
from wtforms import validators


class TicketNoteForm(Form):
    """ Defines the form for pages with the 'page' trait. """

    text = TextAreaField(
        label=_("Text"),
        description=_("Your note about this ticket"),
        validators=[validators.InputRequired()],
        filters=(strip_whitespace, ),
        render_kw={'rows': 10})
