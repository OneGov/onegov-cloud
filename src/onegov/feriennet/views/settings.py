from __future__ import annotations

from markupsafe import Markup
from onegov.core.security import Secret
from onegov.feriennet import _
from onegov.feriennet.app import FeriennetApp
from onegov.feriennet.const import DEFAULT_DONATION_AMOUNTS
from onegov.feriennet.qrbill import beneficiary_to_creditor
from onegov.feriennet.qrbill import qr_iban
from onegov.feriennet.qrbill import swiss_iban
from onegov.feriennet.utils import format_donation_amounts
from onegov.feriennet.utils import parse_donation_amounts
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.validators import Stdnum
from onegov.org.forms.fields import HtmlField
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from stdnum import iban
from wtforms.fields import BooleanField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.fields import URLField
from wtforms.validators import InputRequired
from wtforms.validators import URL
from wtforms.validators import Optional


from typing import TYPE_CHECKING

from onegov.town6.layout import SettingsLayout
if TYPE_CHECKING:
    from onegov.core.types import RenderData
    from onegov.feriennet.request import FeriennetRequest
    from webob import Response


class FeriennetSettingsForm(Form):

    request: FeriennetRequest

    bank_qr_bill = BooleanField(
        label=_('QR-Bill'),
        fieldset=_('Payment')
    )

    bank_account = StringField(
        label=_('Bank Account (IBAN / QR-IBAN)'),
        fieldset=_('Payment'),
        validators=[Stdnum(format='iban')]
    )

    bank_beneficiary = StringField(
        label=_('Beneficiary'),
        fieldset=_('Payment'),
        description=_('Ferienpass Musterlingen, Bahnhofstr. 2, 1234 Beispiel'),
    )

    bank_reference_schema = RadioField(
        label=_('Payment Order'),
        fieldset=_('Payment'),
        choices=[
            ('feriennet-v1', _('Basic')),
            ('esr-v1', _('ESR (General) / QR-Reference')),
            ('raiffeisen-v1', _('ESR (Raiffeisen)'))
        ],
        default='feriennet-v1'
    )

    bank_esr_participant_number = StringField(
        label=_('ESR participant number / QR-IBAN'),
        fieldset=_('Payment'),
        validators=[InputRequired()],
        depends_on=('bank_reference_schema', '!feriennet-v1')
    )

    bank_esr_identification_number = StringField(
        label=_('ESR identification number'),
        fieldset=_('Payment'),
        validators=[InputRequired()],
        depends_on=('bank_reference_schema', 'raiffeisen-v1')
    )

    require_full_age_for_registration = BooleanField(
        label=_('Full age required for registration'),
        fieldset=_('Userprofile'))

    show_political_municipality = BooleanField(
        label=_('Require the political municipality on registration'),
        fieldset=_('Political Municipality'))

    require_swisspass = BooleanField(
        label=_('Require a SwissPass ID of attendees'),
        fieldset=_('SwissPass ID'),
        default=False
    )

    cancellation_conditions = HtmlField(
        label=_('Cancellation condition text'),
        fieldset=_('Cancellation conditions'),
        description=_('The text will be shown below the '
                'confirmation text for an activity in the mail'),
        render_kw={'rows': 10}
    )

    public_organiser_data = MultiCheckboxField(
        label=_('Public organiser data'),
        choices=(
            ('name', _('Name')),
            ('address', _('Address')),
            ('email', _('E-Mail')),
            ('phone', _('Phone')),
            ('website', _('Website'))
        ),
        fieldset=_('Organiser')
    )

    tos_url = URLField(
        label=_('Link to the TOS'),
        description=_('Require users to accept the TOS before booking'),
        fieldset=_('TOS'),
        validators=[URL(), Optional()]
    )

    donation = BooleanField(
        label=_('Donations'),
        description=_('Show a donation button in the invoice view'),
        default=True,
        fieldset=_('Donation'))

    donation_amounts = TextAreaField(
        label=_('Donation Amounts'),
        description=_('One amount per line'),
        depends_on=('donation', 'y'),
        render_kw={'rows': 3},
        fieldset=_('Donation'))

    donation_description = HtmlField(
        label=_('Description'),
        depends_on=('donation', 'y'),
        fieldset=_('Donation'),
        render_kw={'rows': 10})

    volunteers = RadioField(
        label=_('Volunteer registration'),
        fieldset=_('Experimental'),
        choices=[
            ('disabled', _('Disabled')),
            ('admins', _('Only for Admins')),
            ('enabled', _('Enabled')),
        ],
        default='disabled'
    )

    def ensure_beneificary_if_bank_account(self) -> bool | None:
        if self.bank_account.data and not self.bank_beneficiary.data:
            assert isinstance(self.bank_beneficiary.errors, list)
            self.bank_beneficiary.errors.append(_(
                'A beneficiary is required if a bank account is given.'
            ))
            return False
        return None

    def ensure_valid_esr_identification_number(self) -> bool | None:
        if self.bank_reference_schema.data == 'raiffeisen-v1':
            ident = self.bank_esr_identification_number.data or ''

            if not 3 <= len(ident.replace('-', ' ').strip()) <= 6:
                assert isinstance(
                    self.bank_esr_identification_number.errors, list)
                self.bank_esr_identification_number.errors.append(_(
                    'The ESR identification number must be 3-6 characters long'
                ))
                return False
        return None

    def ensure_valid_qr_bill_settings(self) -> bool | None:
        if self.bank_qr_bill.data:
            if not self.bank_account.data:
                assert isinstance(self.bank_qr_bill.errors, list)
                self.bank_qr_bill.errors.append(_('QR-Bills require an IBAN'))
                return False

            if not iban.is_valid(self.bank_account.data):
                assert isinstance(self.bank_account.errors, list)
                self.bank_account.errors.append(_('Not a valid IBAN'))
                return False

            if not swiss_iban(self.bank_account.data):
                assert isinstance(self.bank_account.errors, list)
                self.bank_account.errors.append(_(
                    'QR-Bills require a Swiss or Lichteinstein IBAN'
                ))
                return False

            if qr_iban(self.bank_account.data):
                if self.bank_reference_schema.data != 'esr-v1':
                    assert isinstance(self.bank_reference_schema.errors, list)
                    self.bank_reference_schema.errors.append(_(
                        'Select ESR (General) / QR-Reference when using the '
                        'given QR-IBAN'
                    ))
                    return False
            else:
                if self.bank_reference_schema.data != 'feriennet-v1':
                    assert isinstance(self.bank_reference_schema.errors, list)
                    self.bank_reference_schema.errors.append(_(
                        'Select Basic when using the given IBAN'
                    ))
                    return False

            if not self.bank_beneficiary.data:
                assert isinstance(self.bank_qr_bill.errors, list)
                self.bank_qr_bill.errors.append(_(
                    'QR-Bills require a beneficiary'
                ))
                return False

            if not beneficiary_to_creditor(self.bank_beneficiary.data):
                assert isinstance(self.bank_beneficiary.errors, list)
                self.bank_beneficiary.errors.append(_(
                    'QR-Bills require the beneficiary to be in the form: '
                    'name, street number, code city'
                ))
                return False
        return None

    def process_obj(self, obj: Organisation) -> None:  # type:ignore[override]
        super().process_obj(obj)

        attributes = (
            ('show_political_municipality', False),
            ('require_swisspass', False),
            ('cancellation_conditions', ''),
            ('require_full_age_for_registration', False),
            ('public_organiser_data', self.request.app.public_organiser_data),
            ('bank_account', ''),
            ('bank_beneficiary', ''),
            ('bank_reference_schema', 'feriennet-v1'),
            ('bank_esr_participant_number', ''),
            ('bank_esr_identification_number', ''),
            ('bank_qr_bill', False),
            ('tos_url', ''),
            ('donation', True),
            ('donation_amounts', DEFAULT_DONATION_AMOUNTS),
            ('donation_description', ''),
            ('volunteers', 'disabled'),
        )

        for attr, default in attributes:
            value = obj.meta.get(attr, default)

            if attr == 'donation_amounts':
                value = format_donation_amounts(value)
            elif attr == 'donation_description':
                # NOTE: We need to treat this as Markup
                # TODO: It would be cleaner if we had a proxy object
                #       with all the attributes as dict_property, then
                #       we don't need to do this `attributes` hack
                value = Markup(value)  # nosec: B704

            self[attr].data = value

    def populate_obj(self, obj: Organisation) -> None:  # type:ignore[override]

        attributes = (
            'show_political_municipality',
            'require_swisspass',
            'cancellation_conditions',
            'require_full_age_for_registration',
            'public_organiser_data',
            'bank_account',
            'bank_beneficiary',
            'bank_reference_schema',
            'bank_esr_participant_number',
            'bank_esr_identification_number',
            'bank_qr_bill',
            'tos_url',
            'donation',
            'donation_amounts',
            'donation_description',
            'volunteers',
        )

        super().populate_obj(obj, exclude=attributes)

        for attr in attributes:
            value = self[attr].data

            if attr == 'donation_amounts':
                value = parse_donation_amounts(value)

            obj.meta[attr] = value


@FeriennetApp.form(model=Organisation, name='feriennet-settings',
                   template='form.pt', permission=Secret,
                   form=FeriennetSettingsForm, setting=_('Feriennet'),
                   icon='fa-child')
def custom_handle_settings(
    self: Organisation,
    request: FeriennetRequest,
    form: FeriennetSettingsForm
) -> RenderData | Response:
    return handle_generic_settings(self, request, form, _('Feriennet'),
                                   SettingsLayout(self, request))
