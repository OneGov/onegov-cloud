from decimal import Decimal
from onegov.form import decimal_range


def test_decimal_range():
    assert list(decimal_range('0', '2')) == [
        Decimal('0'),
        Decimal('1')
    ]

    assert list(decimal_range('2', '0')) == [
        Decimal('2'),
        Decimal('1')
    ]

    assert list(decimal_range('0', '1', '0.25')) == [
        Decimal('0'),
        Decimal('0.25'),
        Decimal('0.5'),
        Decimal('0.75')
    ]

    assert decimal_range('0', '1') == decimal_range('0', '1')
    assert decimal_range('1', '0') != decimal_range('0', '1')
    assert decimal_range('0', '1', '0.1') != decimal_range('0', '1', '0.2')

    assert repr(decimal_range('0', '1')) == "decimal_range('0', '1')"
