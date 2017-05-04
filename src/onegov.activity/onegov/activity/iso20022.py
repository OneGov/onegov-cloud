import re

from collections import defaultdict, namedtuple, Counter
from datetime import date
from decimal import Decimal
from itertools import groupby
from lxml import etree
from onegov.activity.models import InvoiceItem
from onegov.activity.utils import encode_invoice_code
from pprint import pformat


DOCUMENT_NS_EX = re.compile(r'.*<Document [^>]+>(.*)')
INVALID_CODE_CHARS_EX = re.compile(r'[^Q0-9A-F]+')
CODE_EX = re.compile(r'Q{1}[A-F0-9]{10}')


def normalize_xml(xml):
    # let's not bother with namespaces at all
    return DOCUMENT_NS_EX.sub(r'<Document>\1', xml)


class Transaction(object):

    __slots__ = (
        'amount',
        'booking_date',
        'booking_text',
        'confidence',
        'credit',
        'currency',
        'debitor',
        'debitor_account',
        'duplicate',
        'note',
        'paid',
        'reference',
        'tid',
        'username',
        'valuta_date',
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.username = None
        self.confidence = 0
        self.duplicate = False
        self.paid = False

    def __repr__(self):
        return pformat({key: getattr(self, key) for key in self.__slots__})

    @property
    def code(self):
        return extract_code(self.booking_text) or extract_code(self.note)

    @property
    def order(self):
        state = self.state

        if self.valuta_date:
            date = self.valuta_date and (
                self.valuta_date.year * 10000 +
                self.valuta_date.month * 100 +
                self.valuta_date.day
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

    for entry in root.xpath('/Document/BkToCstmrStmt/Stmt/Ntry'):
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


def extract_code(text):
    """ Takes a bunch of text and tries to extract a code from it.

    :return: The code without formatting and in lowercase or None

    """

    if text is None:
        return None

    text = text.replace('\n', '').strip()

    if not text:
        return None

    # ENTER A WORLD WITHOUT LOWERCASE
    text = text.upper()

    # replace all O-s (as in OMG) with 0.
    text = text.replace('O', '0')

    # normalize the text by removing all invalid characters.
    text = INVALID_CODE_CHARS_EX.sub('', text)

    # try to fetch the code
    match = CODE_EX.search(text)

    if match:
        return match.group().lower()
    else:
        return None


def match_camt_053_to_usernames(xml, collection, invoice, currency='CHF'):
    """ Takes an ISO20022 camt.053 file and matches it with the invoice
    items in the :class:`~onegov.activity.collections.InvoiceItemCollection`.

    Raises an error if the given xml cannot be processed.

    :return: A list of transactions found in the xml file, together with
    the matching username and a confidence attribute indicating how
    certain the match is (1.0 indicating a sure match, 0.5 a possible match
    and 0.0 a non-match).

    """

    # Get all paid transaction ids to be mark transactions which were paid
    q = collection.for_invoice(None).query()
    q = q.with_entities(InvoiceItem.tid, InvoiceItem.username)
    q = q.group_by(InvoiceItem.tid, InvoiceItem.username)
    q = q.filter(
        InvoiceItem.paid == True,
        InvoiceItem.source == 'xml'
    )

    paid_transaction_ids = {i.tid: i.username for i in q}

    # Get the items matching the given invoice
    q = collection.for_invoice(invoice).query()
    q = q.with_entities(
        InvoiceItem.username,
        InvoiceItem.code,
        InvoiceItem.amount
    )
    q = q.filter(
        InvoiceItem.paid == False
    )
    q = q.order_by(
        InvoiceItem.username
    )

    # Sum up the items to virtual invoices
    invoices = []
    Invoice = namedtuple('Invoice', ('username', 'code', 'ref', 'amount'))

    def encode(code):
        try:
            return encode_invoice_code(code)
        except (RuntimeError, ValueError):
            return None

    for username, items in groupby(q, key=lambda i: i.username):
        amount = Decimal('0.00')

        for item in items:
            amount += item.amount

        invoices.append(Invoice(
            username=username,
            code=item.code,
            ref=encode(item.code),
            amount=amount
        ))

    # Hash the invoices by code (duplicates are technically possible)
    by_code = defaultdict(list)

    # hash the references as well
    by_ref = defaultdict(list)

    # Hash the invoices by amount (dpulicates are probable)
    by_amount = defaultdict(list)

    for invoice in invoices:
        by_code[invoice.code].append(invoice)
        by_amount[invoice.amount].append(invoice)
        by_ref[invoice.ref].append(invoice)

    # go through the transactions, comparing amount and code for a match
    transactions = tuple(extract_transactions(xml))

    codes = Counter(
        t.code for t in transactions
        if t.code and t.tid not in paid_transaction_ids
    )
    refs = Counter(
        t.reference for t in transactions
        if t.reference and t.tid not in paid_transaction_ids
    )

    for transaction in transactions:

        # credit transactions are completely irrelevant for us
        if not transaction.credit:
            continue

        if transaction.currency != currency:
            yield transaction
            continue

        if transaction.tid in paid_transaction_ids:
            transaction.paid = True
            transaction.username = paid_transaction_ids[transaction.tid]
            transaction.confidence = 1
            yield transaction
            continue

        # duplicate codes/references are marked as such, but not matched
        if codes[transaction.code] > 1 or refs[transaction.reference] > 1:
            transaction.duplicate = True

        if transaction.credit and transaction.currency == currency:
            code = transaction.code
            amnt = transaction.amount
            ref = transaction.reference

            code_usernames = {i.username for i in by_code.get(code, tuple())}
            amnt_usernames = {i.username for i in by_amount.get(amnt, tuple())}
            ref_usernames = {i.username for i in by_ref.get(ref, tuple())}

            combined = amnt_usernames & (code_usernames | ref_usernames)

            if len(combined) == 1:
                transaction.username = next(u for u in combined)
                transaction.confidence = 1.0
            elif len(code_usernames) == 1:
                transaction.username = next(u for u in code_usernames)
                transaction.confidence = 0.5
            elif len(ref_usernames) == 1:
                transaction.username = next(u for u in ref_usernames)
                transaction.confidence = 0.5
            elif len(amnt_usernames) == 1:
                transaction.username = next(u for u in amnt_usernames)
                transaction.confidence = 0.5

        yield transaction
