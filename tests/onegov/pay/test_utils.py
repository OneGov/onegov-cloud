from __future__ import annotations

import pytest

from decimal import Decimal
from unittest.mock import MagicMock
from onegov.pay import Price, round_to_five_rappen
from onegov.pay.utils import InvoiceItemMeta
from onegov.org.utils import apply_price_rounding


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


def test_round_to_five_rappen() -> None:
    r = round_to_five_rappen

    # already on a 5-Rappen boundary
    assert r(Decimal('10.00')) == Decimal('10.00')
    assert r(Decimal('10.05')) == Decimal('10.05')
    assert r(Decimal('10.50')) == Decimal('10.50')

    # round down
    assert r(Decimal('10.01')) == Decimal('10.00')
    assert r(Decimal('10.02')) == Decimal('10.00')
    assert r(Decimal('10.11')) == Decimal('10.10')

    # round up
    assert r(Decimal('10.03')) == Decimal('10.05')
    assert r(Decimal('10.04')) == Decimal('10.05')
    assert r(Decimal('10.13')) == Decimal('10.15')

    # half rounds up (ROUND_HALF_UP)
    assert r(Decimal('10.025')) == Decimal('10.05')
    assert r(Decimal('10.075')) == Decimal('10.10')

    # negative amounts (surcharges/rounding can be negative)
    assert r(Decimal('-0.02')) == Decimal('0.00')
    assert r(Decimal('-0.03')) == Decimal('-0.05')


def _make_request(price_rounding: bool) -> MagicMock:
    request = MagicMock()
    request.app.org.price_rounding = price_rounding
    request.translate.side_effect = lambda s: str(s)
    return request


def _item(unit: str, group: str = 'form') -> InvoiceItemMeta:
    return InvoiceItemMeta(text='Test', group=group, unit=Decimal(unit))


def test_apply_price_rounding_disabled() -> None:
    request = _make_request(price_rounding=False)
    items = [_item('10.03')]
    result = apply_price_rounding(request, items)
    assert len(result) == 1
    assert InvoiceItemMeta.total(result) == Decimal('10.03')


def test_apply_price_rounding_already_rounded() -> None:
    request = _make_request(price_rounding=True)
    items = [_item('10.00')]
    result = apply_price_rounding(request, items)
    # no rounding item added when total is already a multiple of 0.05
    assert len(result) == 1


def test_apply_price_rounding_adds_item() -> None:
    request = _make_request(price_rounding=True)
    items = [_item('10.03')]
    result = apply_price_rounding(request, items)
    assert len(result) == 2
    rounding = result[-1]
    assert rounding.group == 'rounding'
    assert InvoiceItemMeta.total(result) == Decimal('10.05')


def test_apply_price_rounding_rounds_down() -> None:
    request = _make_request(price_rounding=True)
    items = [_item('10.02')]
    result = apply_price_rounding(request, items)
    assert len(result) == 2
    assert result[-1].group == 'rounding'
    assert result[-1].unit == Decimal('-0.02')
    assert InvoiceItemMeta.total(result) == Decimal('10.00')


def test_apply_price_rounding_no_org() -> None:
    request = MagicMock(spec=['app', 'translate'])
    # spec without 'org' means getattr(request.app, 'org', None) → None
    request.app = MagicMock(spec=[])
    items = [_item('10.03')]
    result = apply_price_rounding(request, items)
    assert result is items


def test_apply_price_rounding_empty_list() -> None:
    request = _make_request(price_rounding=True)
    result = apply_price_rounding(request, [])
    assert result == []
