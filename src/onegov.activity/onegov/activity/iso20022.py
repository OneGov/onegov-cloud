import re

from datetime import date
from decimal import Decimal
from lxml import etree
from pprint import pformat

# Extracts the data we're intrested in. See https://xmldataset.readthedocs.io/
profile = """
Document
    BkToCstmrStmt
        Stmt
            Ntry
                ValDt
                    Dt = external_dataset:entry,process:to_date,name:valuta_date
                BookgDt
                    Dt = external_dataset:entry,process:to_date,name:booking_date
                AddtlNtryInf = external_dataset:entry,name:booking_text

                NtryDtls
                    TxDtls
                        __NEW_DATASET__ = transactions
                        __EXTERNAL_VALUE__ = entry:valuta_date:transactions entry:booking_date:transactions entry:booking_text:transactions

                        Amt = dataset:transactions,name:amount

                        Refs
                            Prtry
                                Ref = dataset:transactions,name:reference

                        RmtInf
                            Ustrd = dataset:transactions,name:note

                        CdtDbtInd = dataset:transactions,process:credit_as_bool,name:credit

                        RltdPties
                            Dbtr
                                Nm = dataset:transactions,name:debitor
                            DbtrAcct
                                Id
                                    IBAN = dataset:transactions,name:debitor_account

"""  # noqa


def normalize_xml(xml):
    # let's not bother with namespaces at all
    return re.sub(r'.*<Document [^>]+>(.*)', r'<Document>\1', xml)


class Transaction(object):

    __slots__ = (
        'amount',
        'booking_date',
        'booking_text',
        'credit',
        'currency',
        'debitor',
        'debitor_account',
        'note',
        'reference',
        'valuta_date',
    )

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __repr__(self):
        return pformat({key: getattr(self, key) for key in self.__slots__})


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
                amount=as_decimal(first(d, 'Amt/text()')),
                currency=first(d, 'Amt/@Ccy'),
                reference=first(d, 'Refs/Prtry/Ref/text()'),
                note=joined(d, 'RmtInf/Ustrd/text()'),
                credit=first(d, 'CdtDbtInd/text()') == 'CRDT',
                debitor=first(d, 'RltdPties/Dbtr/Nm/text()'),
                debitor_account=first(d, 'RltdPties/DbtrAcct/Id/IBAN/text()')
            )


def process_camt_053(xml, collection):
    """ Takes an ISO20022 camt.053 file and marks the invoices
    in the given :class:`~onegov.activity.collections.InvoiceItemCollection`
    as paid there are any matches.

    Raises an error if the given xml cannot be processed.

    The method does not change the scope of the given collection, so if it
    contains an applied filter, that filter will be respected (and invoice
    items outside the filter will not be considered).

    :return: Two lists, one with the bookings that could be matched and
    one with the bookings that could not be matched.

    """

    pass
