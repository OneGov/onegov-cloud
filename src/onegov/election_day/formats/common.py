import re

from onegov.core.csv import convert_xls_to_csv
from onegov.core.csv import CSVFile
from onegov.core.errors import AmbiguousColumnsError
from onegov.core.errors import DuplicateColumnNamesError
from onegov.core.errors import EmptyFileError
from onegov.core.errors import EmptyLineInFileError
from onegov.core.errors import InvalidFormatError
from onegov.core.errors import MissingColumnsError
from onegov.election_day import _
from xlrd import XLRDError


EXPATS = (
    # These are used by the BFS but not in the official data!
    9170,  # sg
)


STATI = (
    'unknown',
    'interim',
    'final',
)

BALLOT_TYPES = {'proposal', 'counter-proposal', 'tie-breaker'}


class FileImportError(object):
    __slots__ = ['filename', 'line', 'error']

    def __init__(self, error, line=None, filename=None):
        self.filename = filename
        self.error = error
        self.line = line


def load_csv(
    file, mimetype, expected_headers, filename=None, dialect=None,
    encoding=None, rename_duplicate_column_names=False
):
    """ Loads the given file and returns it as CSV file.

    :return: A tuple CSVFile, FileImportError.

    """
    csv = None
    error = None
    csvfile = file

    if mimetype != 'text/plain':
        try:
            csvfile = convert_xls_to_csv(file, 'Resultate')
            dialect = 'excel'
        except IOError:
            try:
                csvfile = convert_xls_to_csv(file)
                dialect = 'excel'
            except XLRDError:
                error = FileImportError(
                    _("Not a valid xls/xlsx file."),
                    filename=filename
                )
            except NotImplementedError:
                error = FileImportError(
                    _("The xls/xlsx file contains unsupported cells."),
                    filename=filename
                )
            except Exception:
                error = FileImportError(
                    _("Not a valid csv/xls/xlsx file."),
                    filename=filename
                )
        except XLRDError:
            error = FileImportError(
                _("Not a valid xls/xlsx file."),
                filename=filename
            )
        except NotImplementedError:
            error = FileImportError(
                _("The xls/xlsx file contains unsupported cells."),
                filename=filename
            )
        except Exception:
            error = FileImportError(
                _("Not a valid csv/xls/xlsx file."),
                filename=filename
            )

    if error:
        return csv, error

    try:
        csv = CSVFile(
            csvfile,
            expected_headers=expected_headers,
            dialect=dialect,
            encoding=encoding,
            rename_duplicate_column_names=rename_duplicate_column_names
        )
        list(csv.lines)  # Needed to raise correct errors and pass tests
    except MissingColumnsError as e:
        error = FileImportError(
            _(
                "Missing columns: '${cols}'",
                mapping={'cols': ', '.join(e.columns)}
            ),
            filename=filename
        )
    except AmbiguousColumnsError:
        error = FileImportError(
            _(
                "Could not find the expected columns, "
                "make sure all required columns exist and that there are no "
                "extra columns."
            ),
            filename=filename
        )
    except DuplicateColumnNamesError:
        error = FileImportError(
            _("Some column names appear twice."),
            filename=filename
        )
    except InvalidFormatError:
        error = FileImportError(
            _("Not a valid csv/xls/xlsx file."),
            filename=filename
        )
    except EmptyFileError:
        error = FileImportError(
            _("The csv/xls/xlsx file is empty."),
            filename=filename
        )
    except EmptyLineInFileError:
        error = FileImportError(
            _("The file contains an empty line."),
            filename=filename
        )
    except Exception:
        error = FileImportError(
            _("Not a valid csv/xls/xlsx file."),
            filename=filename
        )

    return csv, error


# Verification utils
def line_is_relevant(line, number, district=None):
    if district:
        return line.sortwahlkreis == district and line.sortgeschaeft == number
    return line.sortgeschaeft == number


def validate_integer(line, col, treat_none_as_default=True, default=0):
    """
    Checks line of a csv file for a valid integer.
    Raises an error if the attribute is not there.

    :param line: line object from csv reader
    :param col: attribute of line object
    :param default: default to return if line.col is None
    :param treat_none_as_default: raises ValueError if line.col is None
    :return: integer value of line.col
    """
    result = getattr(line, col)
    if not result:
        if treat_none_as_default:
            return default
        raise ValueError(_('Empty value: ${col}',
                           mapping={'col': col}))
    try:
        return int(result)
    except ValueError:
        raise ValueError(_('Invalid integer: ${col}',
                           mapping={'col': col}))


def validate_float(line, col, treat_none_as_default=True, default=0):
    """
    Checks line of a csv file for a valid float number.
    Raises an error if the attribute is not there.

    :param line: line object from csv reader
    :param col: attribute of line object
    :param default: default to return if line.col is None
    :param treat_none_as_default: raises ValueError if line.col is None
    :return: float value of line.col
    """
    result = getattr(line, col)
    if not result:
        if treat_none_as_default:
            return default
        raise ValueError(_('Empty value: ${col}',
                           mapping={'col': col}))
    try:
        return float(result)
    except ValueError:
        raise ValueError(_('Invalid float number: ${col}',
                           mapping={'col': col}))


def validate_empty(line, col, treat_empty_as_default=True, default=''):
    result = getattr(line, col)
    if result:
        return result
    elif treat_empty_as_default:
        return default
    raise ValueError(_('Empty value: ${col}', mapping={'col': col}))


def validate_list_id(line, col, treat_empty_as_default=True, default='0'):
    """ Used to validate list_id that can also be alphanumeric.
     Example: 03B.04
     Previously, the list_id was also 0 if it was empty.
     """
    result = getattr(line, col)
    if result:
        if re.match(r'^[0-9]+[A-Za-z0-9\.]*$', result):
            return result
        raise ValueError(
            _('Not an alphanumeric: ${col}', mapping={'col': col}))
    elif treat_empty_as_default:
        return default
    raise ValueError(_('Empty value: ${col}', mapping={'col': col}))
