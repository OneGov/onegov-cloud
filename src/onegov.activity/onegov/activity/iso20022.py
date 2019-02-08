import re

from cached_property import cached_property
from collections import defaultdict
from datetime import date
from decimal import Decimal
from lxml import etree
from onegov.activity.collections import InvoiceCollection
from onegov.activity.models import Invoice
from onegov.activity.models import InvoiceItem
from onegov.activity.models import InvoiceReference
from onegov.activity.models.invoice_reference import FeriennetSchema
from onegov.user import User
from sqlalchemy import distinct, func


DOCUMENT_NS_EX = re.compile(r'.*<Document [^>]+>(.*)')


def normalize_xml(xml):
    # let's not bother with namespaces at all
    return DOCUMENT_NS_EX.sub(r'<Document>\1', xml)


class Transaction(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.username = None
        self.confidence = 0
        self.duplicate = False
        self.paid = False

    def __repr__(self):
        return repr(self.__dict__)

    @cached_property
    def references(self):
        return set(self.extract_references())

    def extract_references(self):
        if self.reference:
            yield self.reference

        # currently only one schema supports text extraction, the others are
        # stored in the designated reference field
        schema = FeriennetSchema()

        ref = schema.extract(self.booking_text)
        if ref:
            yield ref

        ref = schema.extract(self.note)
        if ref:
            yield ref

    @property
    def order(self):
        state = self.state

        if self.valuta_date:
            date = self.valuta_date and (
                self.valuta_date.year * 10000
                + self.valuta_date.month * 100
                + self.valuta_date.day
            ) * - 1
        else:
            date = -1

        if state == 'success':
            return 0, date, self.username

        if state == 'paid':
            return 1, date, self.username

        if state == 'duplicate':
            return 2, date, self.username

        if state == 'warning':
            return 3, date, self.username

        return 4, date

    @property
    def state(self):
        if self.paid:
            return 'paid'

        if self.duplicate:
            return 'duplicate'

        if self.confidence == 1:
            return 'success'

        if self.confidence == 0.5:
            return 'warning'

        return 'unknown'


def transaction_entries(root):
    """ Yields the transaction entries from the given Camt.053 or Camt.054
    xml. This works because for our purposes the entries of those two formats
    are identical.

    """

    # camt.053
    for entry in root.xpath('/Document/BkToCstmrStmt/Stmt/Ntry'):
        yield entry

    # camt.054
    for entry in root.xpath('/Document/BkToCstmrDbtCdtNtfctn/Ntfctn/Ntry'):
        yield entry


def extract_transactions(xml):
    root = etree.fromstring(normalize_xml(xml).encode('utf-8'))

    def first(element, xpath):
        elements = element.xpath(xpath)
        return elements[0] if elements else None

    def joined(element, xpath):
        return '\n'.join(element.xpath(xpath))

    def as_decimal(text):
        if text:
            return Decimal(text)

    def as_date(text):
        if text:
            return date(*[int(p) for p in text.split('-')])

    for entry in transaction_entries(root):
        booking_date = as_date(first(entry, 'BookgDt/Dt/text()'))
        valuta_date = as_date(first(entry, 'ValDt/Dt/text()'))
        booking_text = first(entry, 'AddtlNtryInf/text()')

        for d in entry.xpath('NtryDtls/TxDtls'):
            yield Transaction(
                booking_date=booking_date,
                valuta_date=valuta_date,
                booking_text=booking_text,
                tid=first(d, 'Refs/AcctSvcrRef/text()'),
                amount=as_decimal(first(d, 'Amt/text()')),
                currency=first(d, 'Amt/@Ccy'),
                reference=first(d, 'RmtInf/Strd/CdtrRefInf/Ref/text()'),
                note=joined(d, 'RmtInf/Ustrd/text()'),
                credit=first(d, 'CdtDbtInd/text()') == 'CRDT',
                debitor=first(d, 'RltdPties/Dbtr/Nm/text()'),
                debitor_account=first(d, 'RltdPties/DbtrAcct/Id/IBAN/text()'),
            )


def match_iso_20022_to_usernames(xml, session, period_id, currency='CHF'):
    """ Takes an ISO20022 camt.053 file and matches it with the invoice
    items in the database.

    Raises an error if the given xml cannot be processed.

    :return: A list of transactions found in the xml file, together with
    the matching username and a confidence attribute indicating how
    certain the match is (1.0 indicating a sure match, 0.5 a possible match
    and 0.0 a non-match).

    """

    def items(period_id=None):
        invoices = InvoiceCollection(session, period_id=period_id)
        return invoices.query_items().outerjoin(Invoice).outerjoin(User)

    # Get all known transaction ids to check what was already paid
    q = items()
    q = q.with_entities(InvoiceItem.tid, User.username)
    q = q.group_by(InvoiceItem.tid, User.username)
    q = q.filter(
        InvoiceItem.paid == True,
        InvoiceItem.source == 'xml'
    )

    paid_transaction_ids = {i.tid: i.username for i in q}

    # Get a list of reference/username pairs as fallback
    q = session.query(InvoiceReference).outerjoin(Invoice).outerjoin(User)
    q = q.with_entities(InvoiceReference.reference, User.username)

    username_by_ref = dict(q)

    # Get the items matching the given period
    q = items(period_id=period_id).outerjoin(InvoiceReference)
    q = q.with_entities(
        User.username,
        func.sum(InvoiceItem.amount).label('amount'),
        func.array_agg(
            distinct(InvoiceReference.reference)).label('references'))
    q = q.group_by(User.username)
    q = q.filter(InvoiceItem.paid == False)
    q = q.order_by(User.username)

    # Hash the invoices by reference (duplicates possible)
    by_ref = defaultdict(list)

    # Hash the invoices by amount (duplicates probable)
    by_amount = defaultdict(list)

    for record in q:
        for reference in record.references:
            by_ref[reference].append(record)

        by_amount[record.amount].append(record)

    # go through the transactions, comparing amount and code for a match
    transactions = tuple(extract_transactions(xml))

    # mark duplicate transactions
    seen = {}

    for t in transactions:
        for ref in t.references:
            if ref in seen:
                t.duplicate = seen[ref].duplicate = True

            seen[ref] = t

    for t in transactions:

        # credit transactions are completely irrelevant for us
        if not t.credit:
            continue

        if t.currency != currency:
            yield t
            continue

        if t.tid in paid_transaction_ids:
            t.paid = True
            t.username = paid_transaction_ids[t.tid]
            t.confidence = 1
            yield t
            continue

        if t.credit and t.currency == currency:
            amnt_usernames = {i.username for i in by_amount[t.amount]}
            ref_usernames = {
                i.username for ref in t.references for i in by_ref[ref]}

            combined = amnt_usernames & ref_usernames

            if len(combined) == 1:
                t.username = next(u for u in combined)
                t.confidence = 1.0
            elif len(ref_usernames) == 1:
                t.username = next(u for u in ref_usernames)
                t.confidence = 0.5
            elif len(amnt_usernames) == 1:
                t.username = next(u for u in amnt_usernames)
                t.confidence = 0.5

            if not t.confidence:
                for ref in t.references:
                    if ref in username_by_ref:
                        t.username = username_by_ref[ref]
                        t.confidence = 0.5

        yield t
