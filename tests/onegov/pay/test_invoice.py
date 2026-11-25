from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.pay.collections import InvoiceCollection
from onegov.pay.models import InvoiceItem, PaymentProvider


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_invoice_collection_delete(session: Session) -> None:
    invoices = InvoiceCollection(session)
    invoice = invoices.add()
    invoice.add('g', 'item', Decimal('1'), Decimal('1'))

    invoices.delete(invoice)
    assert invoices.query().count() == 0
    assert session.query(InvoiceItem).count() == 0


def test_invoice_collection_delete_without_items(session: Session) -> None:
    invoices = InvoiceCollection(session)
    invoice = invoices.add()

    invoices.delete(invoice)
    assert invoices.query().count() == 0


def test_invoice_collection_delete_raises_on_payment_links(
    session: Session
) -> None:
    invoices = InvoiceCollection(session)
    invoice = invoices.add()
    item = invoice.add('g', 'item', Decimal('1'), Decimal('1'))
    item.payments.append(PaymentProvider().payment(amount=Decimal('1')))
    session.flush()

    with pytest.raises(ValueError):
        invoices.delete(invoice, raise_on_payment_links=True)
