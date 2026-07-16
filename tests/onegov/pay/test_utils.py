from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.pay import InvoiceItemMeta, InvoiceMeta, Price, round_amount
from typing import NamedTuple


def test_price() -> None:
    assert Price(0, 'CHF') == Price(0, 'CHF')
    assert Price(0, 'CHF') < Price(1, 'CHF')
    assert Price(10, 'CHF') + Price(20, 'CHF') == Price(30, 'CHF')
    assert Price.zero() + Price(10, 'CHF') == Price(10, 'CHF')
    assert Price(10, 'CHF') - Price(20, 'CHF') == Price(-10, 'CHF')
    assert Price(10, 'CHF')[0] == Decimal(10)
    assert Price(10, 'CHF')[1] == 'CHF'

    amount, currency, fee, cc = Price(10, 'CHF')
    assert amount == Decimal(10)
    assert currency == 'CHF'
    assert fee == Decimal(0)
    assert cc is False

    assert Price(10, 'CHF').as_dict() == {
        'amount': 10.0,
        'currency': 'CHF',
        'fee': 0,
        'credit_card_payment': False,
    }

    assert str(Price(10, 'CHF')) == '10.00 CHF'
    assert repr(Price(10, 'CHF')) == "Price(Decimal('10'), 'CHF')"


def test_add_price_currency() -> None:
    assert Price(10, 'CHF') + Price(20, None) == Price(30, 'CHF')
    assert Price(10, None) + Price(20, 'CHF') == Price(30, 'CHF')
    with pytest.raises(AssertionError):
        assert Price(10, None) + Price(20, None) == Price(30, 'CHF')


def test_multiply() -> None:
    price = Price(100, 'CHF')
    assert price * Decimal(1) == Price(100, 'CHF')
    assert price * 0.5 == Price(50, 'CHF')
    assert price * 2 == Price(200, 'CHF')
    assert Decimal('.1') * price == Price(10, 'CHF')
    assert 0.25 * price == Price(25, 'CHF')
    assert 5 * price == Price(500, 'CHF')

    # can't multiply prices with fees
    # fees need to be applied after
    with pytest.raises(AssertionError):
        Price(100, 'CHF', 10) * 5


def test_apply_discount() -> None:
    price = Price(100, 'CHF')
    assert price.apply_discount(Decimal(1)) == Price(0, 'CHF')
    assert price.apply_discount(Decimal(.75)) == Price(25, 'CHF')
    assert price.apply_discount(Decimal(.5)) == Price(50, 'CHF')
    assert price.apply_discount(Decimal(.25)) == Price(75, 'CHF')
    assert price.apply_discount(Decimal('.1')) == Price(90, 'CHF')
    assert price.apply_discount(Decimal(-1)) == Price(200, 'CHF')
    assert price.apply_discount(Decimal(-.5)) == Price(150, 'CHF')
    assert price.apply_discount(Decimal(-5)) == Price(600, 'CHF')

    # discounts above 100% are not allowed, since it would lead
    # to negative prices
    with pytest.raises(AssertionError):
        price.apply_discount(Decimal(2))

    with pytest.raises(AssertionError):
        price.apply_discount(Decimal('1.00000001'))

    # can't apply discounts to prices with fees
    # fees need to be applied after discounts
    with pytest.raises(AssertionError):
        Price(100, 'CHF', 10).apply_discount(Decimal(.5))


def test_round_amount_to_five_rappen() -> None:
    def r(amount: str) -> Decimal:
        return round_amount(Decimal(amount), Decimal('0.05'))

    # already on a 5-Rappen boundary
    assert r('10.00') == Decimal('10.00')
    assert r('10.05') == Decimal('10.05')
    assert r('10.50') == Decimal('10.50')

    # round down
    assert r('10.01') == Decimal('10.00')
    assert r('10.02') == Decimal('10.00')
    assert r('10.11') == Decimal('10.10')

    # round up
    assert r('10.03') == Decimal('10.05')
    assert r('10.04') == Decimal('10.05')
    assert r('10.13') == Decimal('10.15')

    # half rounds up (ROUND_HALF_UP)
    assert r('10.025') == Decimal('10.05')
    assert r('10.075') == Decimal('10.10')

    # negative amounts (surcharges/rounding can be negative)
    assert r('-0.02') == Decimal('0.00')
    assert r('-0.03') == Decimal('-0.05')


def test_round_amount_other_bases() -> None:
    assert round_amount(Decimal('10.49'), Decimal('1.00')) == Decimal('10.00')
    assert round_amount(Decimal('10.50'), Decimal('1.00')) == Decimal('11.00')
    assert round_amount(Decimal('10.04'), Decimal('0.10')) == Decimal('10.00')
    assert round_amount(Decimal('10.05'), Decimal('0.10')) == Decimal('10.10')


class FakeInvoiceItem(NamedTuple):
    group: str
    amount: Decimal


class FakeInvoice(NamedTuple):
    items: list[FakeInvoiceItem]

    @property
    def total_amount(self) -> Decimal:
        return sum(
            (item.amount for item in self.items),
            start=Decimal('0'),
        )


def item(unit: str) -> InvoiceItemMeta:
    return InvoiceItemMeta(text='Item', group='form', unit=Decimal(unit))


def test_invoice_meta_no_rounding_base() -> None:
    meta = InvoiceMeta([item('10.02')])
    assert meta.rounding_item is None
    assert list(meta) == meta.items
    assert meta.total == Decimal('10.02')


def test_invoice_meta_already_rounded() -> None:
    meta = InvoiceMeta([item('10.05')], rounding_base=Decimal('0.05'))
    assert meta.rounding_item is None
    assert list(meta) == meta.items
    assert meta.total == Decimal('10.05')


def test_invoice_meta_rounds_down() -> None:
    meta = InvoiceMeta([item('10.02')], rounding_base=Decimal('0.05'))
    assert meta.rounding_item is not None
    assert meta.rounding_item.group == 'rounding'
    assert meta.rounding_item.amount == Decimal('-0.02')
    assert list(meta) == [*meta.items, meta.rounding_item]
    assert meta.total == Decimal('10.00')


def test_invoice_meta_rounds_up() -> None:
    meta = InvoiceMeta([item('10.03')], rounding_base=Decimal('0.05'))
    assert meta.rounding_item is not None
    assert meta.rounding_item.amount == Decimal('0.02')
    assert meta.total == Decimal('10.05')


def test_invoice_meta_empty_items() -> None:
    meta = InvoiceMeta([], rounding_base=Decimal('0.05'))
    assert meta.rounding_item is None
    assert list(meta) == []
    assert meta.total == Decimal('0')


def test_invoice_meta_includes_manual_items() -> None:
    invoice = FakeInvoice(
        [
            FakeInvoiceItem('manual', Decimal('0.01')),
            FakeInvoiceItem('form', Decimal('10.00')),
        ]
    )
    meta = InvoiceMeta(
        [item('10.00')],
        rounding_base=Decimal('0.05'),
        invoice=invoice,  # type: ignore[arg-type]
    )
    assert meta.manual_total == Decimal('0.01')
    assert meta.rounding_item is not None
    assert meta.rounding_item.amount == Decimal('-0.01')
    # the grand total includes manual items and lands on the grid
    assert meta.total == Decimal('10.00')
    assert meta.total_excluding_manual_entries == Decimal('9.99')


def test_invoice_meta_manual_total_already_rounded() -> None:
    invoice = FakeInvoice([FakeInvoiceItem('manual', Decimal('0.05'))])
    meta = InvoiceMeta(
        [item('10.00')],
        rounding_base=Decimal('0.05'),
        invoice=invoice,  # type: ignore[arg-type]
    )
    assert meta.rounding_item is None


def test_invoice_meta_total_changed() -> None:
    meta = InvoiceMeta([item('10.02')], rounding_base=Decimal('0.05'))
    assert meta.total_changed()

    invoice = FakeInvoice(
        [
            FakeInvoiceItem('form', Decimal('10.02')),
            FakeInvoiceItem('rounding', Decimal('-0.02')),
            FakeInvoiceItem('manual', Decimal('5.00')),
        ]
    )
    meta = InvoiceMeta(
        [item('10.02')],
        rounding_base=Decimal('0.05'),
        invoice=invoice,  # type: ignore[arg-type]
    )
    # 10.02 + 5.00 manual rounds to 15.00, matching the invoice total
    assert meta.rounding_item is not None
    assert meta.rounding_item.amount == Decimal('-0.02')
    assert meta.total == Decimal('15.00')
    assert not meta.total_changed()

    # without rounding the total no longer matches the invoice
    meta = InvoiceMeta([item('10.02')], invoice=invoice)  # type: ignore
    assert meta.total_changed()
