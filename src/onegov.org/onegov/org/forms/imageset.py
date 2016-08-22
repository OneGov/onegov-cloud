from onegov.form import Form
from onegov.org import _
from wtforms import RadioField, StringField, TextAreaField, validators


class ImageSetForm(Form):
    title = StringField(_("Title"), [validators.InputRequired()])

    lead = TextAreaField(
        label=_("Lead"),
        description=_("Describes what this photo album is about"),
        render_kw={'rows': 4})

    view = RadioField(
        label=_("View"),
        default='full',
        choices=[
            ('full', _("Full size images")),
            ('grid', _("Grid layout"))
        ])
