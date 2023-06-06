from onegov.core.utils import ensure_scheme
from onegov.form import Form
from onegov.org import _
from wtforms.validators import InputRequired
from wtforms.fields import EmailField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField


class PersonForm(Form):
    """ Form to edit people. """

    salutation = StringField(_("Salutation"))
    academic_title = StringField(_("Academic Title"))

    first_name = StringField(_("First name"), [InputRequired()])
    last_name = StringField(_("Last name"), [InputRequired()])

    function = StringField(_("Function"))

    email = EmailField(_("E-Mail"))
    phone = StringField(_("Phone"))
    phone_direct = StringField(_("Direct Phone Number or Mobile"))
    born = StringField(_("Born"))
    profession = StringField(_("Profession"))
    political_party = StringField(_("Political Party"))
    parliamentary_group = StringField(_("Parliamentary Group"))
    website = StringField(_("Website"), filters=(ensure_scheme, ))
    website_2 = StringField(_("Website 2"), filters=(ensure_scheme, ))

    location_address = TextAreaField(
        label=_("Location address"),
        render_kw={'rows': 2}
    )
    location_code_city = StringField(label=_("Location Code and City"))

    postal_address = TextAreaField(
        label=_("Postal address"),
        render_kw={'rows': 2}
    )
    postal_code_city = StringField(label=_("Postal Code and City"))

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
