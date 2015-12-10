""" Offers tools to deal with csv (and xls, xlsx) files. """

import codecs
import re
import sys
import tempfile
import xlrd

from collections import namedtuple, OrderedDict
from csv import DictWriter, Sniffer, QUOTE_ALL
from csv import reader as csv_reader
from csv import writer as csv_writer
from editdistance import eval as distance
from io import BytesIO, StringIO
from itertools import permutations
from onegov.core import errors
from unidecode import unidecode
from xlsxwriter.workbook import Workbook


VALID_CSV_DELIMITERS = {',', ';', '\t'}
WHITESPACE = re.compile(r'\s+')


class CSVFile(object):

    def __init__(self, csvfile, expected_headers):
        # prepare a reader which always returns utf-8
        encoding = detect_encoding(csvfile)
        if encoding is None:
            raise errors.InvalidFormatError()

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

        encountered_empty_line = False

        for ix, line in enumerate(csv_reader(self.csvfile, self.dialect)):

            # raise an empty line error if we found one somewhere in the
            # middle -> at the end they don't count
            if not line:
                encountered_empty_line = True
                continue

            if line and encountered_empty_line:
                raise errors.EmptyLineInFileError()

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
    """ Since encoding detection is hard to get right (and work correctly
    every time), we limit ourselves here to UTF-8 or CP1252, whichever works
    first. CP1252 is basically the csv format you get if you use windows and
    excel and it is a superset of ISO-8859-1/LATIN1.

    """
    csvfile.seek(0)

    try:
        for line in csvfile.readlines():
            line.decode('utf-8')

        return 'utf-8'
    except UnicodeDecodeError:
        return 'cp1252'


def sniff_dialect(csv):
    """ Takes the given csv string and returns the dialect or None. Works just
    like Python's built in sniffer, just that it is a bit more conservative and
    doesn't just accept any kind of character as csv delimiter.

    """
    if not csv:
        raise errors.EmptyFileError()

    dialect = Sniffer().sniff(csv)

    if dialect.delimiter not in VALID_CSV_DELIMITERS:
        raise errors.InvalidFormatError()

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


def convert_xls_to_csv(xls):
    """ Takes an XLS/XLSX file and returns a csv file using the first
    worksheet found.

    """

    xls.seek(0)

    try:
        excel = xlrd.open_workbook(file_contents=xls.read())
    except UnicodeDecodeError:
        raise IOError(
            "Could not read excel file, "
            "be sure to open the file in binary mode!"
        )

    sheet = excel.sheet_by_index(0)

    # XXX we want the output to be bytes encoded, which is not possible using
    # python's csv module. I'm sure there's a clever way of doing this by
    # using a custom StringIO class which encodes on the fly, but I haven't
    # looked into it yet. So for now a conversion is done with some memory
    # overhead.
    text_output = StringIO()
    writecsv = csv_writer(text_output, quoting=QUOTE_ALL)

    for rownum in range(0, sheet.nrows):
        values = []

        for cell in sheet.row(rownum):

            if cell.ctype == xlrd.XL_CELL_TEXT:
                value = cell.value
            elif cell.ctype in (xlrd.XL_CELL_EMPTY, xlrd.XL_CELL_BLANK):
                value = ''
            elif cell.ctype == xlrd.XL_CELL_NUMBER:
                if cell.value.is_integer():
                    value = str(int(cell.value))
                else:
                    value = str(cell.value)
            elif cell.ctype == xlrd.XL_CELL_DATE:
                value = xlrd.xldate_as_tuple(cell.value, excel.datemode)
                value = value.isoformat()
            else:
                raise NotImplementedError

            values.append(value)

        writecsv.writerow(values)

    text_output.seek(0)
    output = BytesIO()

    for line in text_output.readlines():
        output.write(line.encode('utf-8'))

    return output


def convert_list_of_dicts_to_csv(rows, fields=None):
    """ Takes a list of dictionaries and returns a csv.

    If no fields are provided, all fields are included in the order of the keys
    of the first dict. With regular dictionaries this is random. Use an ordered
    dict or provide a list of fields to have a fixed order.

    The function returns a string created in memory. Therefore this function
    is limited to small-ish datasets.

    """

    if not rows:
        return ''

    fields = fields or rows[0].keys()

    output = StringIO()
    writer = DictWriter(output, fieldnames=fields)

    writer.writeheader()

    for row in rows:
        writer.writerow({field: row[field] for field in fields})

    output.seek(0)
    return output.read()


def convert_list_of_dicts_to_xlsx(rows, fields=None):
    """ Takes a list of dictionaries and returns a xlsx.

    This behaves the same way as :func:`convert_list_of_dicts_to_csv`.

    """

    with tempfile.NamedTemporaryFile() as file:
        workbook = Workbook(file.name, options={'constant_memory': True})
        worksheet = workbook.add_worksheet()

        fields = fields or rows[0].keys()

        # write the header
        worksheet.write_row(0, 0, fields)

        # write the rows
        for r, row in enumerate(rows, start=1):
            worksheet.write_row(r, 0, (row[field] for field in fields))

        workbook.close()

        file.seek(0)
        return file.read()


def parse_header(csv, dialect=None):
    """ Takes the first line of the given csv string and returns the headers.

    Headers are normalized (stripped and normalized) and expected to be
    unique. The dialect is sniffed, if not provided.

    :return: A list of headers in the order of appearance.

    """
    try:
        dialect = dialect or sniff_dialect(csv)
    except errors.InvalidFormatError:
        dialect = None  # let the csv reader try, it might still work
    except errors.EmptyFileError:
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
    :exception:`~onegov.core.errors.DuplicateColumnNamesError` error is raised.

    :return: The matched headers in the order of appearance.

    """

    # for this to work we need unique header names
    if len(headers) != len(set(headers)):
        raise errors.DuplicateColumnNamesError()

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
