from datetime import date
from decimal import Decimal
from onegov.activity.iso20022 import extract_transactions, extract_code


def test_extract_transactions(postfinance_xml):
    transactions = extract_transactions(postfinance_xml)

    t = next(transactions)
    assert t.booking_date == date(2016, 4, 30)
    assert t.valuta_date == date(2016, 4, 30)
    assert t.amount == Decimal('24.00')
    assert t.currency == 'CHF'
    assert t.debitor is None
    assert t.debitor_account is None
    assert t.credit is False
    assert t.reference is None
    assert t.booking_text \
        == "UEBRIGE: 25-9034-2 FÜR KONTOAUSZUG PAPIER TÄGLICH"

    t = next(transactions)
    assert t.amount == Decimal('328.75')

    t = next(transactions)
    assert t.amount == Decimal('200.80')

    t = next(transactions)
    assert t.amount == Decimal('638.15')

    t = next(transactions)
    assert t.amount == Decimal('24.00')

    t = next(transactions)
    assert t.amount == Decimal('35.72')

    t = next(transactions)
    assert t.amount == Decimal('100.00')
    assert t.reference == "000000000002015110002913192"

    t = next(transactions)
    assert t.amount == Decimal('50.00')
    assert t.debitor == "Rutschmann Pia"
    assert t.debitor_account is None

    t = next(transactions)
    assert t.amount == Decimal('200.00')

    t = next(transactions)
    assert t.amount == Decimal('50.00')

    t = next(transactions)
    assert t.amount == Decimal('100.00')
    assert t.credit is True
    assert t.reference == "000000000002016030000535990"

    t = next(transactions)
    assert t.amount == Decimal('200.00')
    assert t.debitor == "Bernasconi Maria"
    assert t.debitor_account == "CH4444444444444444444"

    t = next(transactions)
    assert t.amount == Decimal('50.00')

    t = next(transactions)
    assert t.amount == Decimal('100.00')

    t = next(transactions)
    assert t.amount == Decimal('50.00')

    t = next(transactions)
    assert t.amount == Decimal('100.00')

    t = next(transactions)
    assert t.amount == Decimal('50.00')
    assert t.note == "MUSTER MITTEILUNG"

    t = next(transactions)
    assert t.amount == Decimal('20.00')

    t = next(transactions)
    assert t.amount == Decimal('100.00')
    assert t.note == '\n'.join([
        "MUSTER MITTEILUNG 1",
        "MUSTER MITTEILUNG 2",
        "MUSTER MITTEILUNG 3",
        "MUSTER MITTEILUNG 4",
    ])


def test_extract_code():
    assert extract_code('') is None
    assert extract_code('\n asdf') is None
    assert extract_code('Q-70171-292FA') == 'q70171292fa'
    assert extract_code('B-70171-292FA') is None
    assert extract_code('Q-7o171-292FA') == 'q70171292fa'
    assert extract_code('Q-7o171-292FA') == 'q70171292fa'
    assert extract_code('Q-   7o171292FA') == 'q70171292fa'
    assert extract_code('Q-   7o171  29  ---- 2FA') == 'q70171292fa'
    assert extract_code('Q\n7o171\n292FA') == 'q70171292fa'
