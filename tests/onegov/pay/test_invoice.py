from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.pay.collections import InvoiceCollection
from onegov.pay.models import (
    Invoice,
    InvoiceItem,
    InvoiceReference,
    PaymentProvider,
)
from onegov.pay.models.invoice_reference import (
    ESRSchema,
    FeriennetSchema,
    KNOWN_SCHEMAS,
    RaiffeisenSchema,
    Schema,
)


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_invoice_collection_crud(session: Session) -> None:
    invoices = InvoiceCollection(session)

    invoice = invoices.add(invoicing_party='User A')
    assert invoices.query().count() == 1
    assert invoice.invoicing_party == 'User A'

    invoice.add('group', 'first', Decimal('10'), Decimal('2'))
    invoice.add('group', 'second', Decimal('5'), Decimal('1'), paid=True)

    assert invoices.query_items().count() == 2

    # totals across the collection
    assert invoices.total_amount == Decimal('25.00')
    assert invoices.paid_amount == Decimal('5.00')
    assert invoices.outstanding_amount == Decimal('20.00')
    assert invoices.unpaid_count() == 1


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


def test_invoice_collection_polymorphic_type(session: Session) -> None:
    generic = InvoiceCollection(session, type='*')
    assert generic.model_class is Invoice
    assert generic.item_model_class is InvoiceItem

    typed = InvoiceCollection(session, type='generic', item_type='generic')
    assert typed.model_class is Invoice
    typed.add()
    assert typed.query().count() == 1


def test_invoice_amounts_and_properties(session: Session) -> None:
    invoices = InvoiceCollection(session)
    invoice = invoices.add()

    invoice.add('manual', 'manual entry', Decimal('3'), Decimal('1'))
    invoice.add('normal', 'paid item', Decimal('10'), Decimal('1'), paid=True)
    invoice.add('normal', 'unpaid item', Decimal('7'), Decimal('1'))

    assert invoice.total_amount == Decimal('20.00')
    assert invoice.paid_amount == Decimal('10.00')
    assert invoice.outstanding_amount == Decimal('10.00')
    assert invoice.paid is False
    assert invoice.total_excluding_manual_entries == Decimal('17.00')
    assert invoice.price.amount == Decimal('10.00')
    assert invoice.price.currency == 'CHF'
    # no vat set on any item
    assert invoice.total_vat == Decimal('0.00')

    vat_item = invoice.add('normal', 'vat item', Decimal('10'), Decimal('1'))
    vat_item.vat_rate = Decimal('10')
    assert invoice.total_vat == vat_item.vat


def test_invoice_paid_when_empty(session: Session) -> None:
    invoice = InvoiceCollection(session).add()
    assert invoice.outstanding_amount == Decimal('0')
    assert invoice.paid is True


def test_invoice_item_amount_and_vat() -> None:
    item = InvoiceItem(
        group='g', text='t', unit=Decimal('10'), quantity=Decimal('3')
    )
    assert item.amount == Decimal('30.00')

    # no vat set
    assert item.vat_rate is None
    assert item.net_amount == Decimal('30.00')
    assert item.vat == Decimal('0.00')

    # set vat rate -> factor and back
    item.vat_rate = Decimal('10')
    assert item.vat_factor == Decimal('1.1000')
    assert item.vat_rate == Decimal('10.00')
    assert item.net_amount == round(Decimal('30') / Decimal('1.1'), 2)
    assert item.vat == item.amount - item.net_amount

    # clearing the rate
    item.vat_rate = None
    assert item.vat_factor is None


def test_invoice_item_validate_source() -> None:
    item = InvoiceItem(group='g', text='t')
    for source in (None, 'xml', 'datatrans', 'stripe_connect',
                   'worldline_saferpay'):
        item.source = source
        assert item.source == source

    with pytest.raises(AssertionError):
        item.source = 'invalid'


# --- invoice references / schemas ---------------------------------------


def test_schema_render_bucket() -> None:
    assert Schema.render_bucket('esr-v1') == 'esr-v1'
    bucket = Schema.render_bucket('esr-v1', {'account': '01-100-5'})
    assert bucket.startswith('esr-v1-')
    assert bucket != 'esr-v1'


def test_feriennet_schema() -> None:
    schema = FeriennetSchema()
    assert schema.name == 'feriennet-v1'
    assert KNOWN_SCHEMAS['feriennet-v1'] is FeriennetSchema

    ref = schema.new()
    assert ref.startswith('q')
    assert len(ref) == 11

    up = ref.upper()
    assert schema.format(ref) == f'{up[:1]}-{up[1:6]}-{up[6:]}'

    # bucket without config is just the name
    assert schema.bucket == 'feriennet-v1'


def test_feriennet_extract() -> None:
    schema = FeriennetSchema()
    ref = schema.new()
    human = schema.format(ref)

    assert schema.extract(None) is None
    assert schema.extract('   ') is None
    assert schema.extract('no reference here') is None
    assert schema.extract(human) == ref
    # O gets normalised to 0, lowercase handled, surrounding text ignored
    assert schema.extract(f'Payment note: {human}\nthanks') == ref


def test_esr_schema() -> None:
    schema = ESRSchema()
    ref = schema.new()
    assert len(ref) == 27
    assert ref.isdigit()

    # checksum is valid: recomputing over the first 26 digits matches
    assert schema.checksum(ref[:26]) == ref[26]

    # formatting groups in blocks of five, right aligned
    assert schema.format('000000000000000000000215703') == '2 15703'


def test_raiffeisen_schema() -> None:
    schema = RaiffeisenSchema(esr_identification_number='12345')
    ref = schema.new()
    assert len(ref) == 27
    assert ref.startswith('12345')
    assert schema.checksum(ref[:26]) == ref[26]


def test_invoice_reference_validate_schema(session: Session) -> None:
    with pytest.raises(ValueError):
        InvoiceReference(
            reference='x', schema='does-not-exist', bucket='x'
        ).validate_schema('schema', 'does-not-exist')


def test_invoice_reference_link_and_readable(session: Session) -> None:
    invoices = InvoiceCollection(session)
    invoice = invoices.add()

    schema = FeriennetSchema()
    ref = schema.link(session, invoice)
    assert ref is not None
    assert ref.schema == 'feriennet-v1'
    assert ref.bucket == 'feriennet-v1'
    assert ref.readable == schema.format(ref.reference)

    # the invoice can resolve its reference by bucket
    assert invoice.readable_by_bucket('feriennet-v1') == ref.readable
    assert invoice.readable_by_bucket('unknown') is None

    # linking the same schema twice is a no-op
    assert schema.link(session, invoice) is None

    # optimistic linking skips the lookups but still writes
    other = invoices.add()
    assert schema.link(session, other, optimistic=True) is not None
