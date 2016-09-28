from onegov.feriennet import _
from onegov.core.html import sanitize_html
from onegov.form import Form
from onegov.form.fields import OrderedMultiCheckboxField
from onegov.org.utils import annotate_html
from wtforms import TextField, TextAreaField
from wtforms.validators import InputRequired


TAGS = tuple((tag, tag) for tag in (
    _("Adventure"),
    _("Animals"),
    _("Baking"),
    _("Cinema"),
    _("Computer"),
    _("Cooking"),
    _("Dance"),
    _("Design"),
    _("Handicraft"),
    _("Health"),
    _("Media"),
    _("Museums"),
    _("Music"),
    _("Nature"),
    _("Science"),
    _("Security"),
    _("Sport"),
    _("Styling"),
    _("Theater"),
    _("Trade"),
))


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

    tags = OrderedMultiCheckboxField(
        label=_("Tags"),
        choices=TAGS)
