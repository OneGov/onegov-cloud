from onegov.form import Form, with_options
from onegov.town import _
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextArea


class PersonForm(Form):
    """ Form to edit people. """

    academic_title = StringField(_("Academic Title"))

    first_name = StringField(_("First name"), [validators.InputRequired()])
    last_name = StringField(_("Last name"), [validators.InputRequired()])

    picture_url = StringField(
        label=_("Picture"),
        description=_("URL pointing to the picture")
    )

    email = EmailField(_("E-Mail"))
    phone = StringField(_("Phone"))
    website = StringField(_("Website"))

    address = TextAreaField(
        label=_("Address"),
        widget=with_options(TextArea, rows=5)
    )
