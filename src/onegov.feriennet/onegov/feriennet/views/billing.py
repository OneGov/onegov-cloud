import json

from base64 import b64decode
from gzip import GzipFile
from io import BytesIO
from onegov.activity import Period, PeriodCollection
from onegov.activity import InvoiceItem, InvoiceItemCollection
from onegov.activity.iso20022 import match_camt_053_to_usernames
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.collections import BillingCollection, BillingDetails
from onegov.feriennet.forms import BillingForm, BankStatementImportForm
from onegov.feriennet.layout import BillingCollectionImportLayout
from onegov.feriennet.layout import BillingCollectionLayout
from onegov.feriennet.models import InvoiceAction
from onegov.org.elements import Link
from onegov.user import UserCollection, User
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


@FeriennetApp.view(
    model=BillingCollection,
    request_method='POST',
    name='import-ausfuehren',
    permission=Secret)
def view_execute_import(self, request):
    request.assert_valid_csrf_token()
    cache = request.browser_session['account-statement']

    binary = BytesIO(b64decode(cache['data']))
    xml = GzipFile(filename='', mode='r', fileobj=binary).read()
    xml = xml.decode('utf-8')

    invoice = cache['invoice']
    invoices = InvoiceItemCollection(request.app.session())

    transactions = list(
        match_camt_053_to_usernames(xml, invoices, invoice))

    payments = {
        t.username: t for t in transactions if t.state == 'success'
    }

    if payments:
        invoices = InvoiceItemCollection(request.app.session())
        invoices = invoices.for_invoice(cache['invoice'])
        invoices = invoices.query()
        invoices = invoices.filter(InvoiceItem.username.in_(payments.keys()))

        for invoice in invoices:
            invoice.tid = payments[invoice.username].tid
            invoice.source = 'xml'
            invoice.paid = True

        request.success(_("Imported ${count} payments", mapping={
            'count': len(payments)
        }))
    else:
        request.alert(_("No payments could be imported"))

    del request.browser_session['account-statement']

    @request.after
    def redirect_intercooler(response):
        response.headers.add('X-IC-Redirect', request.link(self))


@FeriennetApp.form(
    model=BillingCollection,
    form=BankStatementImportForm,
    permission=Secret,
    name='import',
    template='billing_import.pt',
)
def view_billing_import(self, request, form):
    uploaded = 'account-statement' in request.browser_session

    if form.submitted(request):
        request.browser_session['account-statement'] = {
            'invoice': form.period.data,
            'data': form.xml.data['data']
        }
        uploaded = True
    elif not request.POST and uploaded:
        del request.browser_session['account-statement']
        uploaded = False

    if uploaded:
        cache = request.browser_session['account-statement']

        binary = BytesIO(b64decode(cache['data']))
        xml = GzipFile(filename='', mode='r', fileobj=binary).read()
        xml = xml.decode('utf-8')

        invoice = cache['invoice']
        invoices = InvoiceItemCollection(request.app.session())

        transactions = list(
            match_camt_053_to_usernames(xml, invoices, invoice))

        if not transactions:
            del request.browser_session['account-statement']
            request.alert(_("No transactions were found in the given file"))
            uploaded = False
            form.xml.data = None
        else:
            transactions.sort(key=lambda t: t.order)
    else:
        transactions = None

    users = UserCollection(request.app.session())
    users = {
        u.username: (u.realname or u.username)
        for u in users.query().with_entities(User.username, User.realname)
    }

    layout = BillingCollectionImportLayout(self, request)

    return {
        'layout': layout,
        'title': _("Import Bank Statement"),
        'form': form if not uploaded else None,
        'button_text': _("Preview"),
        'transactions': transactions,
        'uploaded': uploaded,
        'users': users,
        'user_link': lambda u: request.class_link(
            InvoiceItemCollection, {'username': u}
        ),
        'success_count': transactions and sum(
            1 for t in transactions if t.state == 'success'
        ),
        'model': self,
        'post_url': layout.csrf_protected_url(
            URL(request.link(self, 'import-ausfuehren'))
        )
    }
