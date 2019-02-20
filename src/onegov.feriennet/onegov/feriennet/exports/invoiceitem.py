from onegov.activity import Invoice, InvoiceItem, InvoiceReference
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodExportForm
from onegov.user import User
from sqlalchemy.orm import contains_eager


@FeriennetApp.export(
    id='rechnungspositionen',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_("Invoice Items"),
    explanation=_("Exports invoice items in the given period."),
)
class InvoiceItemExport(FeriennetExport):

    def run(self, form, session):
        return self.rows(session, form.selected_period)

    def rows(self, session, period):
        for item in self.query(session, period):
            yield ((k, v) for k, v in self.fields(item))

    def query(self, session, period):
        q = session.query(InvoiceItem)
        q = q.join(Invoice).join(User).join(InvoiceReference)
        q = q.options(
            contains_eager(InvoiceItem.invoice)
            .contains_eager(Invoice.user)
            .undefer(User.data))
        q = q.options(
            contains_eager(InvoiceItem.invoice)
            .contains_eager(Invoice.references))
        q = q.filter(Invoice.period_id == period.id)
        q = q.order_by(
            User.username,
            InvoiceItem.group,
            InvoiceItem.text
        )

        return q

    def fields(self, item):
        yield from self.invoice_item_fields(item)
        yield from self.user_fields(item.invoice.user)
