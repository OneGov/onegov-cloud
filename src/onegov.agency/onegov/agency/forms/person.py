from onegov.agency import _
from onegov.core.utils import ensure_scheme
from onegov.form import Form
from wtforms import StringField
from wtforms import TextAreaField
from wtforms import validators
from wtforms.fields.html5 import EmailField
from onegov.agency.layouts import ExtendedPersonLayout


def fieldset(name):
    if name in ExtendedPersonLayout.public_fields:
        return _("Public")
    return _("Private")


class ExtendedPersonForm(Form):
    """ Form to edit people. """

    # Public
    academic_title = StringField(
        label=_("Academic Title"),
        fieldset=fieldset('academic_title')
    )
    first_name = StringField(
        label=_("First name"),
        validators=[
            validators.InputRequired()
        ],
        fieldset=fieldset('first_name'),
    )
    last_name = StringField(
        label=_("Last name"),
        validators=[
            validators.InputRequired()
        ],
        fieldset=fieldset('last_name')
    )
    profession = StringField(
        label=_("Profession"),
        fieldset=fieldset('profession')
    )
    political_party = StringField(
        label=_("Political Party"),
        fieldset=fieldset('political_party')
    )
    year = StringField(
        label=_("Year"),
        fieldset=fieldset('year')
    )
    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 5},
        fieldset=fieldset('address')
    )
    phone = StringField(
        label=_("Phone"),
        fieldset=fieldset('phone')
    )
    direct_phone = StringField(
        label=_("Direct Phone"),
        fieldset=fieldset('direct_phone')
    )

    # Private
    salutation = StringField(
        label=_("Salutation"),
        fieldset=fieldset('salutation')
    )
    email = EmailField(
        label=_("Email"),
        fieldset=fieldset('email')
    )
    website = StringField(
        label=_("Website"),
        fieldset=fieldset('website'),
        filters=(ensure_scheme, )
    )
    notes = TextAreaField(
        label=_("Notes"),
        render_kw={'rows': 5},
        fieldset=fieldset('notes')
    )
