from onegov.core.utils import ensure_scheme
from onegov.form import Form
from onegov.org import _
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField


class PersonForm(Form):
    """ Form to edit people. """

    first_name = StringField(_("First name"), [validators.InputRequired()])
    last_name = StringField(_("Last name"), [validators.InputRequired()])

    function = StringField(_("Function"))

    picture_url = StringField(
        label=_("Picture"),
        description=_("URL pointing to the picture"),
        render_kw={'class_': 'image-url'}
    )

    email = EmailField(_("E-Mail"))
    phone = StringField(_("Phone"))
    website = StringField(_("Website"), filters=[ensure_scheme])

    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 5}
    )

    notes = TextAreaField(
        label=_("Notes"),
        description=_("Public extra information about this person"),
        render_kw={'rows': 5}
    )
