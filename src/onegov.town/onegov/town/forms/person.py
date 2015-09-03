from onegov.core.utils import ensure_scheme
from onegov.form import Form, with_options
from onegov.town import _
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextArea


class PersonForm(Form):
    """ Form to edit people. """

    salutation = StringField(_("Salutation"))

    first_name = StringField(_("First name"), [validators.InputRequired()])
    last_name = StringField(_("Last name"), [validators.InputRequired()])

    function = StringField(_("Function"))

    picture_url = StringField(
        label=_("Picture"),
        description=_("URL pointing to the picture")
    )

    email = EmailField(_("E-Mail"))
    phone = StringField(_("Phone"))
    website = StringField(_("Website"), filters=[ensure_scheme])

    address = TextAreaField(
        label=_("Address"),
        widget=with_options(TextArea, rows=5)
    )
