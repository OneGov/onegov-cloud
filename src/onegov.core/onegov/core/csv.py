""" Offers tools to deal with csv (and xls, xlsx) files. """
from __future__ import absolute_import

import sys

from csv import reader as csv_reader, Sniffer
from editdistance import eval as distance
from itertools import permutations
from onegov.core import errors


VALID_CSV_DELIMITERS = {',', ';', '\t'}


def sniff_dialect(csv):
    """ Takes the given csv string and returns the dialect or None. Works just
    like Python's built in sniffer, just that it is a bit more conservative and
    doesn't just accept any kind of character as csv delimiter.

    """
    if not csv:
        return None

    dialect = Sniffer().sniff(csv)

    if dialect.delimiter not in VALID_CSV_DELIMITERS:
        return None

    return dialect


def normalize_header(header):
    return header.strip().lower()


def parse_header(csv, dialect=None):
    """ Takes the first line of the given csv string and returns the headers.

    Headers are normalized (stripped and normalized) and expected to be
    unique. The dialect is sniffed, if not provided.

    :return: A list of headers in the order of appearance.

    """
    if not csv:
        return []

    dialect = dialect or sniff_dialect(csv)
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
