from onegov.feriennet import _
from onegov.form import Form
from wtforms.fields import BooleanField, RadioField


class BillingForm(Form):

    confirm = RadioField(
        label=_("Confirm billing:"),
        default='no',
        choices=[
            ('no', _("No, preview only")),
            ('yes', _("Yes, confirm billing"))
        ]
    )

    sure = BooleanField(
        label=_("I know that this stops all changes including cancellations."),
        default=False,
        depends_on=('confirm', 'yes')
    )

    @property
    def finalize_period(self):
        return self.confirm.data == 'yes' and self.sure.data is True
