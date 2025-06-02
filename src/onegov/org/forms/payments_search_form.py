from onegov.form.core import Form
from onegov.form.fields import DateField, SelectField
from onegov.org import _


class PaymentsSearchForm(Form):

    start_date = DateField(
        label=_('From date'),
        fieldset=_('Filter Payments'),
        required=False
    )

    end_date = DateField(
        label=_('To date'),
        fieldset=_('Filter Payments'),
        required=False
    )

    status = SelectField(
        label=_('Status'),
        fieldset=_('Filter Payments'),
        choices=[
            ('', _('All')),
            ('open', _('Open')),
            ('paid', _('Paid')),
            ('invoiced', _('Invoiced'))
        ],
        default='',
        required=False
    )

    payment_type = SelectField(
        label=_('Payment Type'),
        fieldset=_('Filter Payments'),
        choices=[
            ('', _('All')),
            ('manual', _('Manual')),
            ('provider', _('Payment Provider'))
        ],
        default='',
        required=False
    )
    
