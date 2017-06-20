import hashlib
import lxml
import sedate
import string
import re

from datetime import timedelta
from itertools import chain
from onegov.core.utils import chunks
from pyquery import PyQuery as pq
from random import SystemRandom


GROUP_CODE_CHARS = string.ascii_uppercase + string.digits
GROUP_CODE_LENGTH = 10

CODE_TO_ESR_MAPPING = {
    character: '{:02d}'.format(value) for value, character in chain(
        enumerate(string.digits, start=1),
        enumerate(string.ascii_lowercase, start=11)
    )
}

ESR_TO_CODE_MAPPING = {
    value: key for key, value in CODE_TO_ESR_MAPPING.items()
}

INTERNAL_IMAGE_EX = re.compile(r'.*/storage/[0-9a-z]{64}')


def random_group_code():
    random = SystemRandom()

    return ''.join(
        random.choice(GROUP_CODE_CHARS)
        for _ in range(GROUP_CODE_LENGTH)
    )


def overlaps(range_a, range_b):
    return range_b[0] <= range_a[0] and range_a[0] <= range_b[1] or\
        range_a[0] <= range_b[0] and range_b[0] <= range_a[1]


def merge_ranges(ranges):
    """ Merges the given list of ranges into a list of ranges including only
    exclusive ranges. The ranges are turned into tuples to make them
    hashable.

    """

    ranges = sorted(list(ranges))

    # stack of merged values
    merged = [tuple(ranges[0])]

    for r in ranges:
        if overlaps(merged[-1], r):
            merged[-1] = (merged[-1][0], r[1])
        else:
            merged.append(tuple(r))

    return merged


def generate_checksum(number):
    """ Generates the modulo 10 checksum as required by Postfinance.

    :return: The checksum as integer.

    """

    table = (0, 9, 4, 6, 8, 2, 7, 1, 3, 5)
    carry = 0

    for n in str(number):
        carry = table[(carry + int(n)) % 10]

    return (10 - carry) % 10


def append_checksum(number):
    """ Adds the Postfinance modulo 10 checksum to the given number.

    :return: The given number as string with the checksum appended.

    """
    number = str(number)
    return number + str(generate_checksum(number))


def is_valid_checksum(number):
    """ Takes the given number and verifys the checksum which is assumed to
    be the last digit in the given number.

    :return: True if the checksum digit matches the numbers before it.

    """

    number = str(number)
    return number[-1] == str(generate_checksum(number[:-1]))


def as_invoice_code(invoice, username):
    """ Takes the invoice group and username from an
    :class:`~onegov.activity.models.invoice_item.InvoiceItem` and generates
    a hash unique to this invoice/username combination.

    There's no guarantee that this code is unique for an invoice, though
    the chance of it overlapping is very very small -> any algorithm
    doing some kind of matching has to account for this fact.

    We can solve this by introducing a separate invoice record in the future.

    The "q" at the beginning is used as a marker for regular expressions
    (so it's a "q", followed by [a-z0-9]{8}), as well as a version
    identifier.

    If this code changes be aware that the esr encoding/decoding might have
    to be changed as well.

    """

    return 'q' + ''.join((
        hashlib.sha1((invoice + username).encode('utf-8')).hexdigest()[:5],
        hashlib.sha1(username.encode('utf-8')).hexdigest()[:5]
    ))


def format_invoice_code(code):
    """ Takes the invoice code and formats it in a human readable way. """

    code = code.upper()

    return '-'.join((
        code[:1],
        code[1:6],
        code[6:]
    ))


def encode_invoice_code(code):
    """ Takes an invoice code and encodes it as a valid ESR reference with
    checksum included.

    """

    # we prepend a version number in front of the code which goes from
    # 1-9, so we have that many tries to get it right ;)
    version = '1'

    blocks = [version]

    for char in code:
        if char in CODE_TO_ESR_MAPPING:
            blocks.append(CODE_TO_ESR_MAPPING[char])
        else:
            raise RuntimeError("Invalid character {} in {}".format(char, code))

    return append_checksum('{:0>26}'.format(''.join(blocks)))


def decode_esr_reference(reference):
    """ Takes an ESR reference and decodes it into an invoice code if possible.

    Raises an error if the given reference cannot be decoded.

    Handles formatted refences as well as unformatted ones.

    """
    reference = reference.replace(' ', '')

    if len(reference) > 27:
        raise RuntimeError("ESR reference is too long")

    if not is_valid_checksum(reference):
        raise RuntimeError("ESR reference has an invalid checksum")

    reference = reference.lstrip('0')
    version, encoded = reference[0], reference[1:-1]

    if version != '1':
        raise RuntimeError("Unknown ESR reference version: {}".format(version))

    if len(reference) < 22:
        raise RuntimeError("ESR reference is too short")

    if len(reference) % 2 != 0:
        raise RuntimeError("ESR reference has an uneven number of digits")

    blocks = []

    for items in chunks(encoded, 2):
        char = ''.join(items)

        # at this point all characters are going to be valid
        # by virtue of our checksum check
        blocks.append(ESR_TO_CODE_MAPPING[char])

    return ''.join(blocks)


def format_esr_reference(reference):
    """ Takes an ESR reference and formats it in a human-readable way. """
    reference = reference.lstrip('0')
    reference = reference.replace(' ', '')

    blocks = []

    for values in chunks(reversed(reference), n=5, fillvalue=''):
        blocks.append(''.join(reversed(values)))

    return ' '.join(reversed(blocks))


def generate_xml(payments):
    """ Creates an xml for import through ISO20022. Used for testing only. """

    transactions = []

    default = {
        'reference': '',
        'note': ''
    }

    for ix, payment in enumerate(payments):

        if 'tid' not in payment:
            payment['tid'] = 'T{}'.format(ix)

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
            <Refs>
                <AcctSvcrRef>{tid}</AcctSvcrRef>
            </Refs>
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


def dates_overlap(a, b, minutes_between=0, cut_end=True):
    """ Returns true if any time tuple in the list of tuples in a overlaps
    with a time tuple in b.

    """
    # this can be done with an O(n log n) algorithm but since we are
    # operating on a very small n the constant factors dominate and there
    # are fewer constant factors in this approach:

    offset = timedelta(seconds=minutes_between / 2 * 60)
    ms = cut_end and timedelta(microseconds=1) or timedelta()

    # make sure that 11:00 - 12:00 and 12:00 - 13:00 are not overlapping
    ms = timedelta(microseconds=1)

    for s, e in a:
        for os, oe in b:
            if sedate.overlaps(
                s - offset, e + offset - ms,
                os - offset, oe + offset - ms
            ):
                return True

    return False


def is_internal_image(url):
    return url and INTERNAL_IMAGE_EX.match(url) and True or False


def extract_thumbnail(text):

    try:
        first_image = next((img for img in pq(text or '')('img')), None)
    except lxml.etree.XMLSyntaxError:
        first_image = None

    if first_image is None:
        return None

    url = first_image.attrib.get('src')

    if is_internal_image(url) and not url.endswith('/thumbnail'):
        url += '/thumbnail'

    return url
