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
        list(csv.lines)
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
    else:
        return line.sortgeschaeft == number


def validate_integer(line, col, none_be_zero=True):
    """
    Checks line of a csv file for a valid integer.

    :param line: line object from csv reader
    :param col: attribute of line object
    :param none_be_zero: raises ValueError if line.col is None
    :return: integer value of line.col
    """
    assert hasattr(line, col), 'Check done in load_csv'
    try:
        if none_be_zero:
            return int(getattr(line, col) or 0)
        else:
            return int(getattr(line, col))
    except ValueError:
        raise ValueError(_('Invalid integer: ${col}',
                           mapping={'col': col}))
    except TypeError:
        # raises error if none_be_zero=False and the integer is None
        raise ValueError(_('Empty value: ${col}',
                           mapping={'col': col}))


# Helpers
def print_errors(errors):
    error_list = sorted([
        (e.filename, e.line, e.error.interpolate()) for e in errors
    ])
    for fn, l, err in error_list:
        print(f'{fn}:{l} {err}')
