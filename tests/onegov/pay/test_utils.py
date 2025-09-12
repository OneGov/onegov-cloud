from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.pay import Price


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
