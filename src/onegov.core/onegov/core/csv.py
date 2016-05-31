""" Offers tools to deal with csv (and xls, xlsx) files. """

import codecs
import re
import sys
import tempfile
import xlrd

from collections import namedtuple, OrderedDict
from csv import DictWriter, Sniffer, QUOTE_ALL
from csv import Error as CsvError
from csv import reader as csv_reader
from csv import writer as csv_writer
from editdistance import eval as distance
from io import BytesIO, StringIO
from itertools import permutations
from onegov.core import errors
from ordered_set import OrderedSet
from unidecode import unidecode
from xlsxwriter.workbook import Workbook


VALID_CSV_DELIMITERS = {',', ';', '\t'}
WHITESPACE = re.compile(r'\s+')


class CSVFile(object):
    """ Provides access to a csv file.

    :param csvfile:
        The csv file to be accessed. Must be an open file (not a poth), opened
        in binary mode. For example::

            with open(path, 'rb') as f:
                csv = CSVFile(f)

    :param expected_headers:
        The expected headers if known. Expected headers are headers which
        *must* exist in the CSV file. There may be additional headers.

        If the headers are slightly misspelled, a matching algorithm tries to
        guess the correct header, without accidentally matching the wrong
        headers.

        See :func:`match_headers` for more information.

        If the no expected_headers are passed, no checks are done, but the
        headers are still available. Headers matching is useful if a user
        provides the CSV and it might be wrong.

        If it is impossible for misspellings to occurr, the expected headers
        don't have to be specified.

    :param dialect:
        The CSV dialect to expect. By default, the dialect will be guessed
        using Python's heuristic.

    Once the csv file is open, the records can be acceessed as follows::

        with open(path, 'rb') as f:
            csv = CSVFile(f)

            for line in csv.lines:
                csv.my_field  # access the column with the 'my_field' header

    """

    def __init__(self, csvfile, expected_headers=None, dialect=None):

        # prepare a reader which always returns utf-8
        encoding = detect_encoding(csvfile)
        if encoding is None:
            raise errors.InvalidFormatError()

        self.csvfile = codecs.getreader(encoding)(csvfile)

        # sniff the dialect if not already provided
        try:
            self.csvfile.seek(0)
            self.dialect = dialect or sniff_dialect(self.csvfile.read(1024))
        except (CsvError, errors.InvalidFormatError):
            self.csvfile.seek(0)
            self.dialect = sniff_dialect(self.csvfile.read())

        # match the headers
        self.csvfile.seek(0)

        # if no expected headers expect, we just take what we can get
        headers = parse_header(self.csvfile.readline(), self.dialect)
        expected_headers = expected_headers or headers

        self.headers = OrderedDict(
            (h, c) for c, h in enumerate(match_headers(
                headers=headers,
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
        result = normalize_header(value)
        for invalid in '- .':
            result = result.replace(invalid, '_')
        while result and result[0] in '_0123456789':
            result = result[1:]
        return result

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


def convert_xls_to_csv(xls, sheet_name=None):
    """ Takes an XLS/XLSX file and returns a csv file using the given worksheet
    name or the first worksheet found.

    """

    xls.seek(0)

    try:
        excel = xlrd.open_workbook(file_contents=xls.read())
    except UnicodeDecodeError:
        raise IOError(
            "Could not read excel file, "
            "be sure to open the file in binary mode!"
        )

    if sheet_name:
        try:
            sheet = excel.sheet_by_name(sheet_name)
        except xlrd.XLRDError:
            raise IOError(
                "Could not find the given sheet in this excel file!"
            )
    else:
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


def get_keys_from_list_of_dicts(rows, key=None, reverse=False):
    """ Returns all keys of a list of dicts in an ordered tuple.

    If the list of dicts is irregular, the keys found in later rows are
    added at the end of the list.

    Note that the order of keys is otherwise defined by the order of the keys
    of the dictionaries. So if ordered dictionaries are used, the order is
    defined. If regular dictionaries are used, the order is undefined.

    Alternatively, a key and a reverse flag may be provided which will be
    used to order the fields. If the list of fields is specified, the key and
    the reverse flag is ignored.

    """
    fields = OrderedSet()

    for dictionary in rows:
        fields.update(dictionary.keys())

    if key:
        fields = tuple(sorted(fields, key=key, reverse=reverse))
    else:
        fields = tuple(fields)

    return fields


def convert_list_of_dicts_to_csv(rows, fields=None, key=None, reverse=False):
    """ Takes a list of dictionaries and returns a csv.

    If no fields are provided, all fields are included in the order of the keys
    of the first dict. With regular dictionaries this is random. Use an ordered
    dict or provide a list of fields to have a fixed order.

    Alternatively, a key and a reverse flag may be provided which will be
    used to order the fields. If the list of fields is specified, the key and
    the reverse flag is ignored.

    The function returns a string created in memory. Therefore this function
    is limited to small-ish datasets.

    """

    if not rows:
        return ''

    fields = fields or get_keys_from_list_of_dicts(rows, key, reverse)

    output = StringIO()
    writer = DictWriter(output, fieldnames=fields)

    writer.writeheader()

    for row in rows:
        writer.writerow({field: row.get(field, '') for field in fields})

    output.seek(0)
    return output.read()


def convert_list_of_dicts_to_xlsx(rows, fields=None, key=None, reverse=False):
    """ Takes a list of dictionaries and returns a xlsx.

    This behaves the same way as :func:`convert_list_of_dicts_to_csv`.

    """

    with tempfile.NamedTemporaryFile() as file:
        workbook = Workbook(file.name, options={'constant_memory': True})
        worksheet = workbook.add_worksheet()

        fields = fields or get_keys_from_list_of_dicts(rows, key, reverse)

        # write the header
        worksheet.write_row(0, 0, fields)

        # write the rows
        for r, row in enumerate(rows, start=1):
            worksheet.write_row(r, 0, (row.get(field, '') for field in fields))

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
    headers = [normalize_header(h) for h in headers if h]

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
