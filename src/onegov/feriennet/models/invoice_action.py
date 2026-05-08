from __future__ import annotations

from functools import cached_property
from datetime import date
from onegov.activity import ActivityInvoiceItem


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Collection, Iterator
    from sqlalchemy.orm import Session
    from uuid import UUID


class InvoiceAction:

    def __init__(
        self,
        session: Session,
        id: UUID,
        action: Literal['mark-paid', 'mark-unpaid', 'remove-manual'],
        extend_to: Literal['invoice', 'family'] | None = None,
        text: str | None = None
    ) -> None:
        self.session = session
        self.id = id
        self.action = action
        self.extend_to = extend_to
        self.text = text

    @cached_property
    def item(self) -> ActivityInvoiceItem | None:
        return self.session.query(ActivityInvoiceItem
            ).filter_by(id=self.id).first()

    @property
    def valid(self) -> bool:
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
    def targets(self) -> Iterator[ActivityInvoiceItem]:
        item = self.item

        if item:
            yield item

            if self.extend_to == 'invoice':
                q = self.session.query(ActivityInvoiceItem)
                q = q.filter(ActivityInvoiceItem.id != item.id)
                q = q.filter(ActivityInvoiceItem.invoice_id == item.invoice_id)

                yield from q

            if self.extend_to == 'family':
                q = self.session.query(ActivityInvoiceItem)
                q = q.filter(ActivityInvoiceItem.id != item.id)
                q = q.filter(ActivityInvoiceItem.family == item.family)

                yield from q

    def execute(self) -> None:
        if self.action == 'mark-paid':
            self.execute_mark_paid(tuple(self.targets))

        elif self.action == 'mark-unpaid':
            self.execute_mark_unpaid(tuple(self.targets))

        elif self.action == 'remove-manual':
            assert self.extend_to in (None, 'family')
            self.execute_remove_manual(tuple(self.targets))

        else:
            raise NotImplementedError()

    def assert_safe_to_change(
        self,
        targets: Collection[ActivityInvoiceItem]
    ) -> None:
        for target in targets:
            if target.invoice.disable_changes_for_items((target, )):
                raise RuntimeError('Item was paid online')

    def execute_mark_paid(
        self,
        targets: Collection[ActivityInvoiceItem]
    ) -> None:
        self.assert_safe_to_change(targets)

        for target in targets:
            target.payment_date = date.today()
            target.paid = True

    def execute_mark_unpaid(
        self,
        targets: Collection[ActivityInvoiceItem]
    ) -> None:
        self.assert_safe_to_change(targets)

        for target in targets:
            target.payment_date = None
            target.paid = False
            target.tid = None
            target.source = None

    def execute_remove_manual(
        self,
        targets: Collection[ActivityInvoiceItem]
    ) -> None:

        self.assert_safe_to_change(targets)

        for target in targets:
            assert target.family and target.family.startswith('manual-')
            self.session.delete(target)
