import lxml
import random
import re
import sedate
import string

from datetime import date, timedelta
from functools import partial
from pyquery import PyQuery as pq

INTERNAL_IMAGE_EX = re.compile(r'.*/storage/[0-9a-z]{64}')

NUM_RANGE_RE = re.compile(r'\d+-\d+')
DATE_RANGE_RE = re.compile(r'\d{4}-\d{2}-\d{2}:\d{4}-\d{2}-\d{2}')

MUNICIPALITY_EX = re.compile(r"""
    (?P<zipcode>[1-9]{1}[0-9]{3})
    \s+
    (?P<municipality>[\w\s\(\)\.\-]+)
""", re.VERBOSE)


GROUP_CODE_EX = re.compile(r'[A-Z]{3}-?[A-Z]{3}-?[A-Z]{3}')


def random_group_code():
    # 26^9 should be a decent amount of codes to randomly chose, without
    # having to check their uniqueness
    raw = ''.join(random.choice(string.ascii_uppercase) for x in range(9))

    return '-'.join((raw[:3], raw[3:6], raw[-3:]))


def is_valid_group_code(code):
    return GROUP_CODE_EX.match(code) and True or False


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


def num_range_decode(s):
    if not isinstance(s, str):
        return None

    if not NUM_RANGE_RE.match(s):
        return None

    age_range = tuple(int(a) for a in s.split('-'))

    if age_range[0] <= age_range[1]:
        return age_range
    else:
        return None


def num_range_encode(a):
    return '-'.join(str(n) for n in a)


def date_range_decode(s):
    if not isinstance(s, str):
        return None

    if not DATE_RANGE_RE.match(s):
        return None

    s, e = s.split(':')

    return (
        date(*tuple(int(p) for p in s.split('-'))),
        date(*tuple(int(p) for p in e.split('-')))
    )


def date_range_encode(d):
    return ':'.join((d[0].strftime('%Y-%m-%d'), d[1].strftime('%Y-%m-%d')))


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


def dates_overlap(a, b, minutes_between=0, cut_end=True, alignment=None):
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

    if alignment:

        # alignment function
        align = getattr(sedate, f'align_range_to_{alignment}')

        # it is highliy unlikely that this will ever be anything else as this
        # module is pretty much tailored for Switzerland
        align = partial(align, timezone='Europe/Zurich')

    for s, e in a:
        for os, oe in b:

            if alignment:
                s, e = align(s, e)
                os, oe = align(os, oe)

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
    except (lxml.etree.XMLSyntaxError, lxml.etree.ParserError):
        first_image = None

    if first_image is None:
        return None

    url = first_image.attrib.get('src')

    if is_internal_image(url) and not url.endswith('/thumbnail'):
        url += '/thumbnail'

    return url


def extract_municipality(text):
    for line in text.splitlines():
        for fragment in line.split(','):
            match = MUNICIPALITY_EX.match(fragment.strip())

            if match:
                return int(match.group('zipcode')), match.group('municipality')
