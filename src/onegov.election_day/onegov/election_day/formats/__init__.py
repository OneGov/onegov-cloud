from onegov.core.csv import CSVFile, convert_xls_to_csv
from onegov.core.errors import (
    AmbiguousColumnsError,
    DuplicateColumnNamesError,
    EmptyFileError,
    EmptyLineInFileError,
    InvalidFormatError,
    MissingColumnsError,
)
from onegov.election_day import _
from xlrd import XLRDError


class FileImportError(object):
    __slots__ = ['filename', 'line', 'error']

    def __init__(self, error, line=None, filename=None):
        self.filename = filename
        self.error = error
        self.line = line


def load_csv(file, mimetype, expected_headers, filename=None):
    """ Loads the given file and returns it as CSV file.

    :return: A tuple CSVFile, FileImportError.

    """
    csv = None
    error = None
    csvfile = file

    if mimetype != 'text/plain':
        try:
            csvfile = convert_xls_to_csv(file, 'Resultate')
        except IOError:
            try:
                csvfile = convert_xls_to_csv(file)
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

    if error:
        return csv, error

    try:
        csv = CSVFile(csvfile, expected_headers=expected_headers)
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

    return csv, error
