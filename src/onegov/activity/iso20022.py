from __future__ import annotations

import re
import stdnum.ch.esr as esr

from collections import defaultdict
from functools import cached_property
from datetime import date
from decimal import Decimal
from lxml import etree
from onegov.activity.collections import BookingPeriodInvoiceCollection
from onegov.activity.models import BookingPeriodInvoice
from onegov.activity.models import ActivityInvoiceItem
from onegov.pay.models import InvoiceReference
from onegov.pay.models.invoice_reference import FeriennetSchema
from onegov.user import User
from sqlalchemy import func


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from sqlalchemy.orm import Query, Session
    from uuid import UUID


DOCUMENT_NS_EX = re.compile(r'.*<Document [^>]+>(.*)')


def normalize_xml(xml: str) -> str:
    # let's not bother with namespaces at all
    return DOCUMENT_NS_EX.sub(r'<Document>\1', xml)


class Transaction:

    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.username = ''  # Has to be str for comparison used in sort
        self.confidence = 0.0
        self.duplicate = False
        self.paid = False

    def __repr__(self) -> str:
        return repr(self.__dict__)

    if TYPE_CHECKING:
        # let mypy know that this can have arbitrary attributes
        # FIXME: We should just specify all the attributes we put into
        #        the Transaction...
        def __getattr__(self, name: str) -> Any: ...

    @cached_property
    def references(self) -> set[str]:
        if self.invoice_schema == 'feriennet-v1' or not self.reference:
            return set(self.extract_references())
        # if possible, don't rely on manual extraction of the reference number.
        return {self.reference}

    def extract_references(self) -> Iterator[str]:
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
    def order(self) -> tuple[int, int] | tuple[int, int, str]:
        state = self.state

        if self.valuta_date:
            date = -int(self.valuta_date.strftime('%Y%M%d'))
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
    def state(self) -> str:
        if self.paid:
            return 'paid'

        if self.duplicate:
            return 'duplicate'

        if self.confidence == 1:
            return 'success'

        if self.confidence == 0.5:
            return 'warning'

        return 'unknown'


def transaction_entries(root: etree._Element) -> Iterator[etree._Element]:
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


def get_esr(booking_text: str) -> str | None:

    """
    Extracts the QR-bill reference number from the given text.
    QR-bill reference numbers are usually 26 or 27 characters long but can
    be of any length.
    The 27-character version includes a check digit at the
    end. The 26-character version doesn't include the check digit.
    For any other length we don't know if the check digit is included or not.

    For example:

    input: 'Gutschrift QRR: 27 99029 05678 18860 27295 37059'
    output: '269902905678188602729537059'

    :returns: The extracted reference number or None if no reference number.
    If the extracted reference number is only 26 characters long, the check
    digit is appended to the end.
    """

    def format_esr(esr_ref: str) -> str:
        """
        For DB comparison we need the ESR number with leading zeros but no
        spaces.

        """
        return esr.compact(esr_ref).zfill(27)

    # Pattern for any length ESR numbers
    pattern = r'(\d\s*){1,27}'

    match = re.search(pattern, booking_text)
    if match:
        esr_ref = re.sub(r'\s', '', match.group(0))
        if esr.is_valid(esr_ref):
            return format_esr(esr_ref)

        try:
            esr.validate(esr_ref)
        except esr.InvalidChecksum:
            esr_ref = esr_ref[:26]
            check = esr.calc_check_digit(esr_ref)
            return format_esr(esr_ref + check)

    # If no match found, return None
    return None


def extract_transactions(
    xml: str,
    invoice_schema: str
) -> Iterator[Transaction]:
    root = etree.fromstring(normalize_xml(xml).encode('utf-8'))

    def first(element: etree._Element, xpath: str) -> Any | None:
        elements = element.xpath(xpath)
        return elements[0] if elements else None

    def joined(element: etree._Element, xpath: str) -> str:
        return '\n'.join(element.xpath(xpath))

    def as_decimal(text: str | None) -> Decimal | None:
        return Decimal(text) if text else None

    def as_date(text: str | None) -> date | None:
        return date.fromisoformat(text) if text else None

    for entry in transaction_entries(root):
        booking_date = as_date(first(entry, 'BookgDt/Dt/text()'))
        valuta_date = as_date(first(entry, 'ValDt/Dt/text()'))
        booking_text = first(entry, 'AddtlNtryInf/text()')

        # Usually there are multiple TxDtls per Ntry
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
                debitor_account=first(
                    d, 'RltdPties/DbtrAcct/Id/IBAN/text()'),
                invoice_schema=invoice_schema
            )

        # Postfinance QR entries have no TxDtls, but there reference number is
        # in AddtlNtryInf
        if not entry.xpath('NtryDtls/TxDtls') and entry.xpath('AddtlNtryInf'):
            reference = get_esr(str(booking_text))
            yield Transaction(
                booking_date=booking_date,
                valuta_date=valuta_date,
                booking_text=booking_text,
                tid=reference,
                amount=as_decimal(first(entry, 'Amt/text()')),
                currency=first(entry, 'Amt/@Ccy'),
                reference=reference,
                note=joined(entry, 'RmtInf/Ustrd/text()'),
                credit=first(entry, 'CdtDbtInd/text()') == 'CRDT',
                debitor=first(entry, 'RltdPties/Dbtr/Nm/text()'),
                debitor_account=first(
                    entry, 'RltdPties/DbtrAcct/Id/IBAN/text()'),
                invoice_schema=invoice_schema
            )


def match_iso_20022_to_usernames(
    xml: str,
    session: Session,
    period_id: UUID,
    schema: str,
    currency: str = 'CHF'
) -> Iterator[Transaction]:
    """ Takes an ISO20022 camt.053 file and matches it with the invoice
    items in the database.

    Raises an error if the given xml cannot be processed.

    :return: An iterator of transactions found in the xml file, together with
        the matching username and a confidence attribute indicating how
        certain the match is (1.0 indicating a sure match, 0.5 a possible match
        and 0.0 a non-match).

    """

    def items(period_id: UUID | None = None) -> Query[ActivityInvoiceItem]:
        invoices = BookingPeriodInvoiceCollection(session, period_id=period_id)
        return invoices.query_items().outerjoin(
            BookingPeriodInvoice).outerjoin(User)

    # Get all known transaction ids to check what was already paid
    q1 = items().with_entities(ActivityInvoiceItem.tid, User.username)
    q1 = q1.group_by(ActivityInvoiceItem.tid, User.username)
    q1 = q1.filter(
        ActivityInvoiceItem.paid == True,
        ActivityInvoiceItem.source == 'xml'
    )

    paid_transaction_ids = {i.tid: i.username for i in q1}

    # Get a list of reference/username pairs as fallback
    q2 = session.query(InvoiceReference).outerjoin(
        BookingPeriodInvoice).outerjoin(User)
    username_by_ref = dict(q2.with_entities(
        InvoiceReference.reference,
        User.username
    ).tuples())

    # Get the items matching the given period
    q3 = items(period_id=period_id).outerjoin(InvoiceReference).with_entities(
        User.username,
        func.sum(ActivityInvoiceItem.amount).label('amount'),
        InvoiceReference.reference,
    )
    q3 = q3.group_by(User.username, InvoiceReference.reference)
    q3 = q3.filter(ActivityInvoiceItem.paid == False)
    q3 = q3.order_by(User.username)

    # Hash the invoices by reference (duplicates possible)
    by_ref = defaultdict(list)

    # Hash the invoices by amount (duplicates probable)
    by_amount = defaultdict(list)

    last_username = None

    for record in q3:
        by_ref[record.reference].append(record)

        if last_username != record.username:
            by_amount[record.amount].append(record)
            last_username = record.username

    # go through the transactions, comparing amount and code for a match
    transactions = tuple(extract_transactions(xml, schema))

    # mark duplicate transactions
    seen: dict[str, Transaction] = {}

    for t in transactions:
        for ref in t.references:
            if ref in seen:
                t.duplicate = seen[ref].duplicate = True

            seen[ref] = t

    for t in transactions:

        # debit transactions are completely irrelevant for us
        if not t.credit:
            continue

        if t.currency != currency:
            yield t
            continue
        if t.tid and t.tid in paid_transaction_ids:
            # what if tid is None?
            # it so happened that the records uploaded were marked as paid
            # for all records with tid = None since it was in paid_transactions
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
