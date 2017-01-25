from datetime import date
from decimal import Decimal
from onegov.activity.collections import InvoiceItemCollection
from onegov.activity.iso20022 import extract_transactions, extract_code
from onegov.activity.iso20022 import match_camt_053_to_usernames


def generate_xml(payments):
    transactions = []

    default = {
        'reference': '',
        'note': ''
    }

    for payment in payments:

        if payment['amount'].startswith('-'):
            payment['credit'] = 'DBIT'
        else:
            payment['credit'] = 'CRDT'

        payment['currency'] = payment['amount'][-3:]
        payment['amount'] = payment['amount'].strip('-+')[:-3]

        for key in default:
            if key not in payment:
                payment[key] = default[key]

        transactions.append("""
        <TxDtls>
            <Amt Ccy="{currency}">{amount}</Amt>
            <CdtDbtInd>{credit}</CdtDbtInd>
            <RmtInf>
                <Strd>
                    <CdtrRefInf>
                        <Ref>{reference}</Ref>
                    </CdtrRefInf>
                </Strd>
                <Ustrd>{note}</Ustrd>
            </RmtInf>
        </TxDtls>
        """.format(**payment))

    return """<?xml version="1.0" encoding="UTF-8"?>
        <Document>
            <BkToCstmrStmt>
                <Stmt>
                    <Ntry>
                        <NtryDtls>
                            {}
                        </NtryDtls>
                    </Ntry>
                </Stmt>
            </BkToCstmrStmt>
        </Document>
    """.format('\n'.join(transactions))


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
    assert extract_code('Code: q-70171-292fa') == 'q70171292fa'


def test_invoice_matching_without_esr(session, owner, member):
    items = InvoiceItemCollection(session)

    i1 = items.add(owner, '2017', 'Aaron', 'Billard', 250, 1)
    i2 = items.add(owner, '2017', 'Baron', 'Pokemon', 250, 1)

    assert i1.code == i2.code

    i3 = items.add(member, '2017', 'Connie', 'Swimming', 250, 1)
    i4 = items.add(member, '2018', 'Donnie', 'Football', 250, 1)

    assert i3.code != i4.code

    # match against a perfect match and one with a wrong amount
    xml = generate_xml([
        dict(amount='500.00 CHF', note=i1.code),
        dict(amount='500.00 CHF', note=i3.code)
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2017'))

    assert len(transactions) == 2
    assert transactions[0].amount == Decimal(500.00)
    assert transactions[0].username == owner.username
    assert transactions[0].note == i1.code == i2.code
    assert transactions[0].confidence == 1.0
    assert transactions[1].amount == Decimal(500.00)
    assert transactions[1].username == member.username
    assert transactions[1].note == i3.code
    assert transactions[1].confidence == 0.5

    # match against debits
    xml = generate_xml([
        dict(amount='-500.00 CHF', note=i1.code),
        dict(amount='-500.00 CHF', note=i3.code)
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2017'))

    assert len(transactions) == 2
    assert transactions[0].amount == Decimal(500.00)
    assert transactions[0].credit is False
    assert transactions[0].username is None
    assert transactions[1].amount == Decimal(500.00)
    assert transactions[1].credit is False
    assert transactions[1].username is None

    # match against a code with extra information
    xml = generate_xml([
        dict(amount='500.00 CHF', note='Code: ' + i1.code),
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2017'))

    assert len(transactions) == 1
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0

    # match against transactions from a different invoice
    xml = generate_xml([
        dict(amount='500.00 CHF', note=i1.code),
        dict(amount='250.00 CHF', note=i3.code),
        dict(amount='250.00 CHF', note=i4.code),
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2018'))

    assert len(transactions) == 3
    assert transactions[0].amount == Decimal(500.00)
    assert transactions[0].username is None
    assert transactions[0].confidence == 0
    assert transactions[1].amount == Decimal(250.00)
    assert transactions[1].username == member.username
    assert transactions[1].confidence == 0.5
    assert transactions[2].amount == Decimal(250.00)
    assert transactions[2].username == member.username
    assert transactions[2].confidence == 1.0

    # match against the wrong currency
    xml = generate_xml([
        dict(amount='250.00 EUR', note=i4.code),
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2018'))

    assert len(transactions) == 1
    assert transactions[0].username is None
    assert transactions[0].confidence == 0

    # match against the wrong code
    xml = generate_xml([
        dict(amount='250.00 CHF', note='asdf'),
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2018'))
    assert len(transactions) == 1
    assert transactions[0].username == member.username
    assert transactions[0].confidence == 0.5

    # match against the wrong code and wrong amount
    xml = generate_xml([
        dict(amount='123.00 CHF', note='asdf'),
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2018'))
    assert len(transactions) == 1
    assert transactions[0].username is None
    assert transactions[0].confidence == 0

    # match against duplicate bookings
    xml = generate_xml([
        dict(amount='250.00 CHF', note=i4.code),
        dict(amount='250.00 CHF', note=i4.code),
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2018'))
    assert len(transactions) == 2
    assert transactions[0].username is None
    assert transactions[0].confidence == 0
    assert transactions[0].duplicate is True
    assert transactions[0].username is None
    assert transactions[0].confidence == 0
    assert transactions[0].duplicate is True

    # match against split bookings
    xml = generate_xml([
        dict(amount='125.00 CHF', note=i1.code),
        dict(amount='125.00 CHF', note=i1.code),
    ])

    transactions = list(match_camt_053_to_usernames(xml, items, '2018'))
    assert len(transactions) == 2
    assert transactions[0].username is None
    assert transactions[0].confidence == 0
    assert transactions[0].duplicate is True
    assert transactions[0].username is None
    assert transactions[0].confidence == 0
    assert transactions[0].duplicate is True
