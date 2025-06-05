from __future__ import annotations

from wtforms import DateField
from onegov.form.core import Form
from onegov.form.fields import SelectField
from onegov.org import _


class PaymentSearchForm(Form):

    start_date = DateField(
        label=_('From date'),
        fieldset=_('Filter Payments'),
    )

    end_date = DateField(
        label=_('To date'),
        fieldset=_('Filter Payments'),
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
    )
