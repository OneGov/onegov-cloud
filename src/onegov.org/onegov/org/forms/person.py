from onegov.core.utils import ensure_scheme
from onegov.form import Form
from onegov.org import _
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField


class PersonForm(Form):
    """ Form to edit people. """

    salutation = StringField(_("Salutation"))
    academic_title = StringField(_("Academic Title"))

    first_name = StringField(_("First name"), [validators.InputRequired()])
    last_name = StringField(_("Last name"), [validators.InputRequired()])

    function = StringField(_("Function"))

    email = EmailField(_("E-Mail"))
    phone = StringField(_("Phone"))
    phone_direct = StringField(_("Direct Phone Number"))
    born = StringField(_("Born"))
    profession = StringField(_("Profession"))
    political_party = StringField(_("Political Party"))
    website = StringField(_("Website"), filters=(ensure_scheme, ))

    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 5}
    )

    picture_url = StringField(
        label=_("Picture"),
        description=_("URL pointing to the picture"),
        render_kw={'class_': 'image-url'}
    )

    notes = TextAreaField(
        label=_("Notes"),
        description=_("Public extra information about this person"),
        render_kw={'rows': 5}
    )
