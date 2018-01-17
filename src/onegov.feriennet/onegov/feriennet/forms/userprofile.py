import string

from onegov.feriennet import _
from onegov.feriennet.utils import encode_name, decode_name
from onegov.form import Form
from onegov.form.validators import Stdnum
from wtforms import BooleanField, StringField, TextAreaField, RadioField
from wtforms.fields.html5 import URLField
from wtforms.validators import Optional, URL, ValidationError, InputRequired


class UserProfileForm(Form):
    """ Custom userprofile form for feriennet """

    extra_fields = (
        'salutation',
        'organisation',
        'address',
        'zip_code',
        'place',
        'email',
        'phone',
        'website',
        'emergency',
        'daily_ticket_statistics',
        'bank_account',
        'bank_beneficiary',
        'political_municipality'
    )

    salutation = RadioField(
        label=_("Salutation"),
        choices=[
            ('mr', _("Mr.")),
            ('ms', _("Ms.")),
        ],
        validators=[InputRequired()]
    )

    first_name = StringField(
        label=_("First Name"),
        validators=[InputRequired()]
    )

    last_name = StringField(
        label=_("Last Name"),
        validators=[InputRequired()]
    )

    organisation = StringField(
        label=_("Organisation"),
    )

    address = TextAreaField(
        label=_("Address"),
        render_kw={'rows': 4},
    )

    zip_code = StringField(
        label=_("Zip Code"),
        validators=[InputRequired()]
    )

    place = StringField(
        label=_("Place"),
        validators=[InputRequired()]
    )

    political_municipality = StringField(
        label=_("Political Municipality"),
        validators=[InputRequired()]
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

    bank_account = StringField(
        label=_("Bank Account (IBAN)"),
        validators=[Stdnum(format='iban')]
    )

    bank_beneficiary = StringField(
        label=_("Beneficiary"),
    )

    daily_ticket_statistics = BooleanField(
        _("Send a daily status e-mail.")
    )

    @property
    def name(self):
        return encode_name(
            self.first_name.data.strip(),
            self.last_name.data.strip()
        )

    @name.setter
    def name(self, value):
        self.first_name.data, self.last_name.data = decode_name(value)

    def on_request(self):
        self.toggle_political_municipality()
        self.toggle_daily_ticket_statistics()

    @property
    def show_political_municipality(self):
        return self.request.app.org.meta.get('show_political_municipality')

    def toggle_political_municipality(self):
        if not self.show_political_municipality:
            self.delete_field('political_municipality')

    @property
    def show_daily_ticket_statistics(self):
        roles = self.request.app.settings.org.status_mail_roles
        return self.request.current_role in roles

    def toggle_daily_ticket_statistics(self):
        if not self.show_daily_ticket_statistics:
            self.delete_field('daily_ticket_statistics')

    def validate_emergency(self, field):
        if field.data:
            characters = tuple(c for c in field.data if c.strip())

            numbers = sum(1 for c in characters if c in string.digits)
            chars = sum(1 for c in characters if c in string.ascii_letters)

            if numbers < 9 or chars < 5:
                raise ValidationError(
                    _("Please enter both a phone number and a name"))

    def ensure_beneificary_if_bank_account(self):
        if self.bank_account.data and not self.bank_beneficiary.data:
            self.bank_beneficiary.errors.append(_(
                "A beneficiary is required if a bank account is given."
            ))
            return False

    def should_skip_key(self, key):
        if key == 'political_municipality':
            if not self.show_political_municipality:
                return True

        if key == 'daily_ticket_statistics':
            if not self.show_daily_ticket_statistics:
                return True

        return False

    def populate_obj(self, model):
        super().populate_obj(model)

        if model:
            model.data = model.data or {}
            model.realname = self.name

            for key in self.extra_fields:

                if self.should_skip_key(key):
                    continue

                model.data[key] = self.data.get(key)

                # strip whitespace from all fields
                if isinstance(model.data[key], str):
                    model.data[key] = model.data[key].strip()

    def process_obj(self, model):
        super().process_obj(model)

        if model:
            modeldata = model.data or {}
            self.name = model.realname

            for key in self.extra_fields:

                if self.should_skip_key(key):
                    continue

                getattr(self, key).data = modeldata.get(key)
