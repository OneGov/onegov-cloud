from __future__ import annotations

import string

from wtforms import BooleanField

from onegov.feriennet import _
from onegov.feriennet.utils import encode_name, decode_name
from onegov.form import Form
from onegov.form.validators import Stdnum
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import Optional, URL, ValidationError, InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.feriennet.request import FeriennetRequest
    from onegov.user import User


class UserProfileForm(Form):
    """ Custom userprofile form for feriennet """

    request: FeriennetRequest

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
        'ticket_statistics',
        'bank_account',
        'bank_beneficiary',
        'political_municipality',
        'show_contact_data_to_others',
    )

    ticket_statistics = RadioField(
        label=_('Send a periodic status e-mail.'),
        fieldset=_('General'),
        default='weekly',
        validators=[InputRequired()],
        choices=(
            ('daily', _(
                'Daily (exluding the weekend)')),
            ('weekly', _(
                'Weekly (on mondays)')),
            ('monthly', _(
                'Monthly (on first monday of the month)')),
            ('never', _(
                'Never')),
        )
    )

    salutation = RadioField(
        label=_('Salutation'),
        fieldset=_('Personal'),
        choices=[
            ('mr', _('Mr.')),
            ('ms', _('Ms.')),
        ],
        validators=[InputRequired()]
    )

    first_name = StringField(
        label=_('First Name'),
        fieldset=_('Personal'),
        validators=[InputRequired()]
    )

    last_name = StringField(
        label=_('Last Name'),
        fieldset=_('Personal'),
        validators=[InputRequired()]
    )

    organisation = StringField(
        label=_('Organisation'),
        fieldset=_('Personal'),
    )

    address = TextAreaField(
        label=_('Address'),
        fieldset=_('Personal'),
        render_kw={'rows': 4},
        validators=[InputRequired()]
    )

    zip_code = StringField(
        label=_('Zip Code'),
        fieldset=_('Personal'),
        validators=[InputRequired()]
    )

    place = StringField(
        label=_('Place'),
        fieldset=_('Personal'),
        validators=[InputRequired()]
    )

    political_municipality = StringField(
        label=_('Political Municipality'),
        fieldset=_('Personal'),
        validators=[InputRequired()]
    )

    email = StringField(
        label=_('Public E-Mail Address'),
        fieldset=_('Personal'),
        description=_('If different than username')
    )

    phone = StringField(
        label=_('Phone'),
        fieldset=_('Personal'),
    )

    emergency = StringField(
        label=_('Emergency Contact'),
        fieldset=_('Personal'),
        description=_('012 345 67 89 (Peter Muster)'),
        validators=[InputRequired()]
    )

    website = URLField(
        label=_('Website'),
        fieldset=_('Personal'),
        description=_('Website address including http:// or https://'),
        validators=[Optional(), URL()]
    )

    bank_account = StringField(
        label=_('Bank Account (IBAN)'),
        fieldset=_('Personal'),
        validators=[Stdnum(format='iban')]
    )

    bank_beneficiary = StringField(
        label=_('Beneficiary'),
        fieldset=_('Personal'),
    )

    show_contact_data_to_others = BooleanField(
        label=_('Allow contact for carpooling'),
        fieldset=_('Privacy'),
        default=False
    )

    @property
    def name(self) -> str:
        assert self.first_name.data is not None
        assert self.last_name.data is not None
        return encode_name(
            self.first_name.data.strip(),
            self.last_name.data.strip()
        )

    @name.setter
    def name(self, value: str) -> None:
        self.first_name.data, self.last_name.data = decode_name(value)

    def on_request(self) -> None:
        self.toggle_political_municipality()
        self.toggle_ticket_statistics()

    @property
    def show_political_municipality(self) -> bool | None:
        return self.request.app.org.meta.get('show_political_municipality')

    def toggle_political_municipality(self) -> None:
        if not self.show_political_municipality:
            self.delete_field('political_municipality')

    @property
    def show_ticket_statistics(self) -> bool:
        roles = self.request.app.settings.org.status_mail_roles
        return self.request.current_role in roles

    def toggle_ticket_statistics(self) -> None:
        if not self.show_ticket_statistics:
            self.delete_field('ticket_statistics')

    def validate_emergency(self, field: StringField) -> None:
        if field.data:
            characters = tuple(c for c in field.data if c.strip())

            numbers = sum(1 for c in characters if c in string.digits)
            chars = sum(1 for c in characters if c in string.ascii_letters)

            if numbers < 9 or chars < 5:
                raise ValidationError(
                    _('Please enter both a phone number and a name'))

    def ensure_beneificary_if_bank_account(self) -> bool | None:
        if self.bank_account.data and not self.bank_beneficiary.data:
            assert isinstance(self.bank_beneficiary.errors, list)
            self.bank_beneficiary.errors.append(_(
                'A beneficiary is required if a bank account is given.'
            ))
            return False
        return None

    def should_skip_key(self, key: str) -> bool:
        if key == 'political_municipality':
            if not self.show_political_municipality:
                return True

        if key == 'ticket_statistics':
            if not self.show_ticket_statistics:
                return True

        return False

    def populate_obj(self, model: User) -> None:  # type:ignore[override]
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

    def process_obj(self, model: User) -> None:  # type:ignore[override]
        super().process_obj(model)

        if model:
            modeldata = model.data or {}
            # NOTE: Technically this should always be set, but it could be
            #       empty for externally created users. decode_name can deal
            #       with `None` so we should not assert here, we need an
            #       asymmetric property to model this behavior
            self.name = model.realname  # type:ignore[assignment]

            for key in self.extra_fields:

                if self.should_skip_key(key):
                    continue

                default = getattr(self, key).default
                getattr(self, key).data = modeldata.get(key, default)
