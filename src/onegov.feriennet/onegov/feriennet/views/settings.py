from onegov.core.security import Secret
from onegov.feriennet import _
from onegov.feriennet.app import FeriennetApp
from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.form.validators import Stdnum
from onegov.org.models import Organisation
from onegov.org.views.settings import handle_generic_settings
from wtforms.validators import InputRequired
from wtforms.fields import BooleanField, StringField, RadioField


class FeriennetSettingsForm(Form):

    bank_account = StringField(
        label=_("Bank Account (IBAN)"),
        fieldset=_("Payment"),
        validators=[Stdnum(format='iban')]
    )

    bank_beneficiary = StringField(
        label=_("Beneficiary"),
        fieldset=_("Payment"),
    )

    bank_payment_order_type = RadioField(
        label=_("Payment Order"),
        fieldset=_("Payment"),
        choices=[
            ('basic', _("Basic")),
            ('esr', _("With reference number (ESR)")),
        ],
        default='basic'
    )

    bank_esr_participant_number = StringField(
        label=_("ESR participant number"),
        fieldset=_("Payment"),
        validators=[InputRequired()],
        depends_on=('bank_payment_order_type', 'esr')
    )

    show_political_municipality = BooleanField(
        label=_("Require the political municipality in the userprofile"),
        fieldset=_("Userprofile"))

    show_related_contacts = BooleanField(
        label=_(
            "Parents can see the contacts of other parents in "
            "the same activity"
        ),
        fieldset=_("Privacy")
    )

    public_organiser_data = MultiCheckboxField(
        label=_("Public organiser data"),
        choices=(
            ('name', _("Name")),
            ('address', _("Address")),
            ('email', _("E-Mail")),
            ('phone', _("Phone")),
            ('website', _("Website"))
        ),
        fieldset=_("Organiser")
    )

    def ensure_beneificary_if_bank_account(self):
        if self.bank_account.data and not self.bank_beneficiary.data:
            self.bank_beneficiary.errors.append(_(
                "A beneficiary is required if a bank account is given."
            ))
            return False

    def process_obj(self, obj):
        super().process_obj(obj)

        self.show_political_municipality.data = obj.meta.get(
            'show_political_municipality', False)

        self.show_related_contacts.data = obj.meta.get(
            'show_related_contacts', False)

        self.public_organiser_data.data = obj.meta.get(
            'public_organiser_data', self.request.app.public_organiser_data)

    def populate_obj(self, obj, *args, **kwargs):
        super().populate_obj(obj, *args, **kwargs)

        obj.meta['show_political_municipality']\
            = self.show_political_municipality.data

        obj.meta['show_related_contacts']\
            = self.show_related_contacts.data

        obj.meta['public_organiser_data']\
            = self.public_organiser_data.data


@FeriennetApp.form(model=Organisation, name='feriennet-settings',
                   template='form.pt', permission=Secret,
                   form=FeriennetSettingsForm, setting=_("Feriennet"),
                   icon='fa-child')
def custom_handle_settings(self, request, form):
    return handle_generic_settings(self, request, form, _("Feriennet"))
