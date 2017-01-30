from cached_property import cached_property
from onegov.activity import InvoiceItem, InvoiceItemCollection


class InvoiceAction(object):

    def __init__(self, session, id, action, extend_to=None):
        self.session = session
        self.id = id
        self.action = action
        self.extend_to = extend_to

    @cached_property
    def invoice_items(self):
        return InvoiceItemCollection(self.session)

    @cached_property
    def item(self):
        return self.invoice_items.by_id(self.id)

    @property
    def valid(self):
        if self.action not in ('mark-paid', 'mark-unpaid'):
            return False

        if self.extend_to not in (None, 'invoice'):
            return False

        if not self.item:
            return False

        return True

    @property
    def targets(self):
        item = self.item

        if item:
            yield item

            if self.extend_to == 'invoice':
                q = self.invoice_items.query()
                q = q.filter(InvoiceItem.id != item.id)
                q = q.filter(InvoiceItem.username == item.username)
                q = q.filter(InvoiceItem.invoice == item.invoice)

                yield from q

    def execute(self):
        if self.action == 'mark-paid':
            self.execute_mark_paid(self.targets)

        elif self.action == 'mark-unpaid':
            self.execute_mark_unpaid(self.targets)

        else:
            raise NotImplementedError()

    def execute_mark_paid(self, targets):
        for target in targets:
            target.paid = True
            assert not target.disable_changes, "item was paid online"

    def execute_mark_unpaid(self, targets):
        for target in targets:
            target.paid = False
            target.tid = None
            target.source = None
            assert not target.disable_changes, "item was paid online"
