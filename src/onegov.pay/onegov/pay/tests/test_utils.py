from decimal import Decimal
from onegov.pay import Price


def test_price():
    assert Price(0, 'CHF') == Price(0, 'CHF')
    assert Price(0, 'CHF') < Price(1, 'CHF')
    assert Price(10, 'CHF') + Price(20, 'CHF') == Price(30, 'CHF')
    assert Price.zero() + Price(10, 'CHF') == Price(10, 'CHF')
    assert Price(10, 'CHF') - Price(20, 'CHF') == Price(-10, 'CHF')
    assert Price(10, 'CHF')[0] == Decimal(10)
    assert Price(10, 'CHF')[1] == 'CHF'

    amount, currency, fee = Price(10, 'CHF')
    assert amount == Decimal(10)
    assert currency == 'CHF'
    assert fee == Decimal(0)

    assert Price(10, 'CHF').as_dict() == {
        'amount': 10.0,
        'currency': 'CHF',
        'fee': 0
    }

    assert str(Price(10, 'CHF')) == '10.00 CHF'
    assert repr(Price(10, 'CHF')) == "Price(Decimal('10'), 'CHF')"
