import json

from onegov.activity import Period, PeriodCollection
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection, BillingDetails
from onegov.feriennet.forms import BillingForm
from onegov.feriennet.layout import BillingCollectionLayout
from onegov.feriennet.models import InvoiceAction
from onegov.org.elements import Link
from purl import URL


def all_periods(request):
    p = PeriodCollection(request.app.session()).query()
    p = p.order_by(Period.execution_start)
    return p.all()


@FeriennetApp.form(
    model=BillingCollection,
    form=BillingForm,
    template='billing.pt',
    permission=Secret)
def view_billing(self, request, form):
    layout = BillingCollectionLayout(self, request)
    session = request.app.session

    if form.submitted(request) and not self.period.finalized:
        self.create_invoices(
            all_inclusive_booking_text=request.translate(_("Passport"))
        )

        if form.finalize_period:
            self.period.finalized = True

    # we can generate many links here, so we need this to be
    # as quick as possible, which is why we only use one token
    csrf_token = request.new_csrf_token().decode('utf-8')

    def insert_csrf(url):
        return URL(url).query_param('csrf-token', csrf_token).as_string()

    def invoice_actions(details):
        return actions(details.first, details.paid, 'invoice')

    def item_actions(item):
        return actions(item, item.paid)

    def actions(item, paid, extend_to=None):
        if self.period.finalized:
            if paid:
                yield Link(
                    text=(
                        extend_to and
                        _("Mark whole bill as unpaid") or
                        _("Mark as unpaid")
                    ),
                    classes=('mark-unpaid', ),
                    request_method='POST',
                    url=insert_csrf(request.link(InvoiceAction(
                        session=session,
                        id=item.id,
                        action='mark-unpaid',
                        extend_to=extend_to
                    )))
                )
            else:
                yield Link(
                    text=(
                        extend_to and
                        _("Mark whole bill as paid") or
                        _("Mark as paid")
                    ),
                    classes=('mark-paid', ),
                    request_method='POST',
                    url=insert_csrf(request.link(InvoiceAction(
                        session=session,
                        id=item.id,
                        action='mark-paid',
                        extend_to=extend_to
                    )))
                )

    return {
        'layout': layout,
        'title': _("Billing for ${title}", mapping={
            'title': self.period.title
        }),
        'model': self,
        'period': self.period,
        'periods': all_periods(request),
        'total': self.total,
        'form': form,
        'outstanding': self.outstanding,
        'button_text': _("Create Bills"),
        'invoice_actions': invoice_actions,
        'item_actions': item_actions
    }


@FeriennetApp.view(
    model=InvoiceAction,
    permission=Secret,
    request_method='POST')
def execute_invoice_action(self, request):
    request.assert_valid_csrf_token()
    self.execute()

    @request.after
    def trigger_bill_update(response):
        response.headers.add('X-IC-Trigger', 'reload-from')
        response.headers.add('X-IC-Trigger-Data', json.dumps({
            'selector': '#' + BillingDetails.item_id(self.item)
        }))
