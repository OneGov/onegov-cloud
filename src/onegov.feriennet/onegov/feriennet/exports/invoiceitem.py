from onegov.activity import InvoiceItem
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodExportForm
from sqlalchemy.orm import joinedload


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
        q = q.options(joinedload(InvoiceItem.user))
        q = q.order_by(
            InvoiceItem.username,
            InvoiceItem.group,
            InvoiceItem.text
        )

        return q

    def fields(self, item):
        yield from self.invoice_item_fields(item)
        yield from self.user_fields(item.user)
