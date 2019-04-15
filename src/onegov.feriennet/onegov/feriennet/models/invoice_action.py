from cached_property import cached_property
from onegov.activity import InvoiceItem


class InvoiceAction(object):

    def __init__(self, session, id, action, extend_to=None, text=None):
        self.session = session
        self.id = id
        self.action = action
        self.extend_to = extend_to
        self.text = text

    @cached_property
    def item(self):
        return self.session.query(InvoiceItem).filter_by(id=self.id).first()

    @property
    def valid(self):
        if self.action not in ('mark-paid', 'mark-unpaid', 'remove-manual'):
            return False

        if self.extend_to not in (None, 'invoice', 'family'):
            return False

        if not self.item:
            return False

        if self.extend_to == 'family' and self.action != 'remove-manual':
            return False

        return True

    @property
    def targets(self):
        item = self.item

        if item:
            yield item

            if self.extend_to == 'invoice':
                q = self.session.query(InvoiceItem)
                q = q.filter(InvoiceItem.id != item.id)
                q = q.filter(InvoiceItem.invoice_id == item.invoice_id)

                yield from q

            if self.extend_to == 'family':
                q = self.session.query(InvoiceItem)
                q = q.filter(InvoiceItem.id != item.id)
                q = q.filter(InvoiceItem.family == item.family)

                yield from q

    def execute(self):
        if self.action == 'mark-paid':
            self.execute_mark_paid(tuple(self.targets))

        elif self.action == 'mark-unpaid':
            self.execute_mark_unpaid(tuple(self.targets))

        elif self.action == 'remove-manual':
            assert self.extend_to in (None, 'family')
            self.execute_remove_manual(tuple(self.targets))

        else:
            raise NotImplementedError()

    def assert_safe_to_change(self, targets):
        for target in targets:
            if target.invoice.disable_changes_for_items((target, )):
                raise RuntimeError("Item was paid online")

    def execute_mark_paid(self, targets):
        self.assert_safe_to_change(targets)

        for target in targets:
            target.paid = True

    def execute_mark_unpaid(self, targets):
        self.assert_safe_to_change(targets)

        for target in targets:
            target.paid = False
            target.tid = None
            target.source = None

    def execute_remove_manual(self, targets):
        self.assert_safe_to_change(targets)

        for target in targets:
            assert target.family and target.family.startswith('manual-')
            self.session.delete(target)
