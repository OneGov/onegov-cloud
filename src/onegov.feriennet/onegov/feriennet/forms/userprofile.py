import string

from onegov.feriennet import _
from onegov.form import Form
from wtforms import StringField, TextAreaField
from wtforms.fields.html5 import URLField
from wtforms.validators import Optional, URL, ValidationError, InputRequired


class UserProfileForm(Form):
    """ Custom userprofile form for feriennet """

    extra_fields = ('address', 'email', 'phone', 'website', 'emergency')

    realname = StringField(
        label=_("Name"),
        description=_("Personal-, Society- or Company-Name")
    )

    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 4},
    )

    email = StringField(
        label=_("Public E-Mail Address"),
        description=_("If different than username")
    )

    phone = StringField(
        label=_("Phone")
    )

    emergency = StringField(
        label=_("Emergency Contact"),
        description=_("012 345 67 89 (Peter Muster)"),
        validators=[InputRequired()]
    )

    website = URLField(
        label=_("Website"),
        description=_("Website address including http:// or https://"),
        validators=[Optional(), URL()]
    )

    def validate_emergency(self, field):
        if field.data:
            characters = tuple(c for c in field.data if c.strip())

            numbers = sum(1 for c in characters if c in string.digits)
            chars = sum(1 for c in characters if c in string.ascii_letters)

            if numbers < 9 or chars < 5:
                raise ValidationError(
                    _("Please enter both a phone number and a name"))

    def populate_obj(self, model):
        super().populate_obj(model)

        model.data = model.data or {}
        model.realname = self.realname.data

        for key in self.extra_fields:
            model.data[key] = self.data.get(key)

    def process_obj(self, model):
        super().process_obj(model)

        modeldata = model.data or {}
        self.realname.data = model.realname

        for key in self.extra_fields:
            getattr(self, key).data = modeldata.get(key)
