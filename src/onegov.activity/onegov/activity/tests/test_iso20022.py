from datetime import date
from decimal import Decimal
from onegov.activity.collections import InvoiceCollection
from onegov.activity.iso20022 import extract_transactions
from onegov.activity.iso20022 import match_iso_20022_to_usernames
from onegov.activity.utils import generate_xml


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
    assert t.tid == "20160430001001080060699000901107"

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
    assert t.tid == "160527CH00T3L0NC"

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
    assert t.tid == "160527CH00T3HDBA"
    assert t.note == '\n'.join([
        "MUSTER MITTEILUNG 1",
        "MUSTER MITTEILUNG 2",
        "MUSTER MITTEILUNG 3",
        "MUSTER MITTEILUNG 4",
    ])


def test_unique_transaction_ids(postfinance_xml):
    seen = set()

    for transaction in extract_transactions(postfinance_xml):
        assert transaction.tid not in seen
        seen.add(transaction.tid)


def test_invoice_matching(session, owner, member,
                          prebooking_period, inactive_period):

    p1 = prebooking_period
    p2 = inactive_period

    invoices = InvoiceCollection(session)

    own_i1 = invoices.add(user_id=owner.id, period_id=p1.id)
    mem_i1 = invoices.add(user_id=member.id, period_id=p1.id)
    mem_i2 = invoices.add(user_id=member.id, period_id=p2.id)

    i1 = own_i1.add('Aaron', 'Billard', 250, 1)
    i2 = own_i1.add('Baron', 'Pokemon', 250, 1)
    i3 = mem_i1.add('Connie', 'Swimming', 250, 1)
    i4 = mem_i2.add('Donnie', 'Football', 250, 1)

    # match against a perfect match and one with a wrong amount
    xml = generate_xml([
        dict(amount='500.00 CHF', note=i1.invoice.references[0].reference),
        dict(amount='500.00 CHF', note=i3.invoice.references[0].reference)
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 2
    assert transactions[0].amount == Decimal(500.00)
    assert transactions[0].username == owner.username
    assert transactions[0].note \
        == i1.invoice.references[0].reference \
        == i2.invoice.references[0].reference
    assert transactions[0].confidence == 1.0
    assert transactions[1].amount == Decimal(500.00)
    assert transactions[1].username == member.username
    assert transactions[1].note == i3.invoice.references[0].reference
    assert transactions[1].confidence == 0.5

    # debit transactions are simply ignored
    xml = generate_xml([
        dict(amount='-500.00 CHF', note=i1.invoice.references[0].reference),
        dict(amount='-500.00 CHF', note=i3.invoice.references[0].reference)
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 0

    # match against a code with extra information
    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            note='Code: ' + i1.invoice.references[0].reference
        ),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 1
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0

    # match against transactions from a different invoice
    xml = generate_xml([
        dict(amount='500.00 CHF', note=i1.invoice.references[0].reference),
        dict(amount='250.00 CHF', note=i3.invoice.references[0].reference),
        dict(amount='250.00 CHF', note=i4.invoice.references[0].reference),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p2.id))

    assert len(transactions) == 3
    assert transactions[0].amount == Decimal(500.00)
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 0.5
    assert transactions[1].amount == Decimal(250.00)
    assert transactions[1].username == member.username
    assert transactions[1].confidence == 0.5
    assert transactions[2].amount == Decimal(250.00)
    assert transactions[2].username == member.username
    assert transactions[2].confidence == 1.0

    # match against the wrong currency
    xml = generate_xml([
        dict(amount='250.00 EUR', note=i4.invoice.references[0].reference),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p2.id))

    assert len(transactions) == 1
    assert transactions[0].username is None
    assert transactions[0].confidence == 0

    # match against the wrong code
    xml = generate_xml([
        dict(amount='250.00 CHF', note='asdf'),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p2.id))
    assert len(transactions) == 1
    assert transactions[0].username == member.username
    assert transactions[0].confidence == 0.5

    # match against the wrong code and wrong amount
    xml = generate_xml([
        dict(amount='123.00 CHF', note='asdf'),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p2.id))
    assert len(transactions) == 1
    assert transactions[0].username is None
    assert transactions[0].confidence == 0

    # match against duplicate bookings
    xml = generate_xml([
        dict(amount='250.00 CHF', note=i4.invoice.references[0].reference),
        dict(amount='250.00 CHF', note=i4.invoice.references[0].reference),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p2.id))
    assert len(transactions) == 2
    assert transactions[0].username == member.username
    assert transactions[0].confidence == 1.0
    assert transactions[0].duplicate is True
    assert transactions[0].username == member.username
    assert transactions[0].confidence == 1.0
    assert transactions[0].duplicate is True

    # match against split bookings
    xml = generate_xml([
        dict(amount='125.00 CHF', note=i1.invoice.references[0].reference),
        dict(amount='125.00 CHF', note=i1.invoice.references[0].reference),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p2.id))
    assert len(transactions) == 2
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 0.5
    assert transactions[0].duplicate is True
    assert transactions[1].username == owner.username
    assert transactions[1].confidence == 0.5
    assert transactions[1].duplicate is True

    # match against reference numbers
    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            reference=i1.invoice.references[0].reference
        ),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 1
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0

    # match against a mix of reference numbers and codes
    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            reference=i1.invoice.references[0].reference),
        dict(
            amount='250.00 CHF',
            note=i3.invoice.references[0].reference),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 2
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0
    assert transactions[1].username == member.username
    assert transactions[1].confidence == 1.0

    # ignore invalid esr references
    xml = generate_xml([
        dict(amount='500.00 CHF', reference='booyah'),
        dict(amount='250.00 CHF', note=i3.invoice.references[0].reference),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 2
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 0.5
    assert transactions[1].username == member.username
    assert transactions[1].confidence == 1.0

    # if a single transaction has both reference and code, then one is
    # allowed to be faulty without a confidence penalty
    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            reference=i1.invoice.references[0].reference,
            note=i1.invoice.references[0].reference
        ),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 1
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0

    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            reference='000127131108141601011502061',
            note=i1.invoice.references[0].reference
        ),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 1
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0

    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            reference=i1.invoice.references[0].reference,
            note='qeb3afd0e43'
        ),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))

    assert len(transactions) == 1
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0

    # make sure paid transactions are matched as well (here we basically send
    # a separate bill which completes the outstanding amount)
    i1.paid = True
    i1.tid = 'foobar'
    i1.source = 'xml'

    xml = generate_xml([
        dict(
            amount='250 CHF',
            note=i1.invoice.references[0].reference,
            tid='foobar'),
        dict(
            amount='250 CHF',
            note=i1.invoice.references[0].reference,
            tid=None),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, p1.id))
    assert len(transactions) == 2

    assert transactions[0].tid == 'foobar'
    assert transactions[0].username == owner.username
    assert transactions[0].paid is True

    assert transactions[1].username == owner.username
    assert transactions[1].confidence == 1.0
    assert transactions[1].paid is False


def test_invoice_matching_multischema(session, owner, prebooking_period):
    period = prebooking_period

    # create an invoice with two possible references
    invoices = InvoiceCollection(
        session,
        period_id=period.id,
        user_id=owner.id,
        schema='feriennet-v1')

    i = invoices.add()
    i.add('Aaron', 'Billard', 250, 1)

    invoices.for_schema('esr-v1').schema.link(session, i)

    # make sure we can match against both
    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            note=i.references[0].reference
        ),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, period.id))

    assert len(transactions) == 1
    assert transactions[0].amount == Decimal(500)
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0

    xml = generate_xml([
        dict(
            amount='500.00 CHF',
            reference=i.references[1].reference
        ),
    ])

    transactions = list(match_iso_20022_to_usernames(xml, session, period.id))

    assert len(transactions) == 1
    assert transactions[0].amount == Decimal(500)
    assert transactions[0].username == owner.username
    assert transactions[0].confidence == 1.0
