""" Offers tools to deal with csv (and xls, xlsx) files. """

import codecs
import re
import sys

from chardet.universaldetector import UniversalDetector
from collections import namedtuple, OrderedDict
from csv import reader as csv_reader, Sniffer
from editdistance import eval as distance
from itertools import permutations
from onegov.core import errors
from unidecode import unidecode


VALID_CSV_DELIMITERS = {',', ';', '\t'}
WHITESPACE = re.compile(r'\s+')


class CSVFile(object):

    def __init__(self, csvfile, expected_headers):
        # prepare a reader which always returns utf-8
        csvfile.seek(0)

        encoding = detect_encoding(csvfile)['encoding']
        if encoding is None:
            raise errors.InvalidFormat()

        self.csvfile = codecs.getreader(encoding)(csvfile)

        # find out the dialect
        self.csvfile.seek(0)
        self.dialect = sniff_dialect(self.csvfile.read(1024))

        # match the headers
        self.csvfile.seek(0)
        self.headers = OrderedDict(
            (h, c) for c, h in enumerate(match_headers(
                headers=parse_header(self.csvfile.readline(), self.dialect),
                expected=expected_headers
            ))
        )

        # create an output type
        assert 'rownumber' not in expected_headers, """
            rownumber can't be used as a header
        """

        self.rowtype = namedtuple(
            "CSVFileRow", ['rownumber'] + list(
                self.as_valid_identifier(k)
                for k in self.headers.keys()
            )
        )

    def as_valid_identifier(self, value):
        return normalize_header(value).replace('-', '_').replace(' ', '_')

    @property
    def lines(self):
        self.csvfile.seek(0)

        for ix, line in enumerate(csv_reader(self.csvfile, self.dialect)):

            # the first line is the header
            if ix == 0:
                continue

            yield self.rowtype(
                rownumber=ix + 1,  # row numbers are for customers, not coders
                **{
                    self.as_valid_identifier(header): line[column].strip()
                    for header, column in self.headers.items()
                }
            )


def detect_encoding(csvfile):
    """ Runs the chardet detector incrementally against the given csv file.
    Once it is confident enough, it will return a value.

    See: http://chardet.readthedocs.org/

    """
    detector = UniversalDetector()
    csvfile.seek(0)

    try:
        for line in csvfile:
            detector.feed(line)

            if detector.done:
                break
    finally:
        detector.close()

    return detector.result


def sniff_dialect(csv):
    """ Takes the given csv string and returns the dialect or None. Works just
    like Python's built in sniffer, just that it is a bit more conservative and
    doesn't just accept any kind of character as csv delimiter.

    """
    if not csv:
        raise errors.EmptyFile()

    dialect = Sniffer().sniff(csv)

    if dialect.delimiter not in VALID_CSV_DELIMITERS:
        raise errors.InvalidFormat()

    return dialect


def normalize_header(header):
    """ Normalizes a header value to be as uniform as possible.

    This includes:
        * stripping the whitespace around it
        * lowercasing everything
        * transliterating unicode (e.g. 'ä' becomes 'a')
        * removing duplicate whitespace inside it
    """

    header = header.strip()
    header = header.lower()
    header = unidecode(header)
    header = WHITESPACE.sub(' ', header)

    return header


def parse_header(csv, dialect=None):
    """ Takes the first line of the given csv string and returns the headers.

    Headers are normalized (stripped and normalized) and expected to be
    unique. The dialect is sniffed, if not provided.

    :return: A list of headers in the order of appearance.

    """
    try:
        dialect = dialect or sniff_dialect(csv)
    except errors.InvalidFormat:
        dialect = None  # let the csv reader try, it might still work
    except errors.EmptyFile:
        return []

    headers = next(csv_reader(csv.splitlines(), dialect=dialect))
    headers = [normalize_header(h) for h in headers]

    return headers


def match_headers(headers, expected):
    """ Takes a list of normalized headers and matches them up against a
    list of expected headers.

    The headers may differ from the expected headers. This function tries to
    match them up using the Levenshtein distance. It does so somewhat carefully
    by calculating a sane distance using the input.

    The passed headers are expected to be have been normalized by
    :func:`normalize_header`, since we usually will pass the result of
    :func:`parse_header` to this function.

    For example::

        match_headers(
            headers=['firstname', 'lastname'],
            expected=['last_name', 'first_name']
        )

    Results in::

        ['first_name', 'last_name']

    If no match is possible, an
    :exception:`~onegov.core.errors.MissingColumnsError`, or
    :exception:`~onegov.core.errors.AmbiguousColumnsError` or
    :exception:`~onegov.core.errors.DuplicateColumnNames` error is raised.

    :return: The matched headers in the order of appearance.

    """

    # for this to work we need unique header names
    if len(headers) != len(set(headers)):
        raise errors.DuplicateColumnNames()

    # we calculate a 'sane' levenshtein distance by comparing the
    # the distances between all headers, permutations, as well as the lengths
    # of all expected headers. This makes sure we don't end up with matches
    # that make no sense (like ['first', 'second'] matching ['first', 'third'])
    sane_distance = getattr(sys, 'maxsize', 0) or sys.maxint

    if len(headers) > 1:
        sane_distance = min((
            sane_distance,
            min(distance(a, b) for a, b in permutations(headers, 2))
        ))

    if len(expected) > 1:
        sane_distance = min((
            sane_distance,
            min(distance(a, b) for a, b in permutations(expected, 2))
        ))

    sane_distance = min((
        sane_distance,
        min(len(c) for c in expected)
    ))

    mapping = {}
    missing = []
    ambiguous = {}

    for column in expected:
        normalized = normalize_header(column)
        distances = dict((h, distance(normalized, h)) for h in headers)

        closest = min(distances.values())

        if closest >= sane_distance:
            missing.append(column)
            continue

        matches = tuple(c for c in distances if distances[c] == closest)

        if len(matches) > 1:
            ambiguous[column] = matches
            continue

        mapping[matches[0]] = column

    if missing:
        raise errors.MissingColumnsError(missing)

    if ambiguous:
        raise errors.AmbiguousColumnsError(ambiguous)

    # return the mapping or the original header (we allow for extra headers,
    # we just don't allow for missing headers)
    return [mapping.get(h, h) for h in headers]
