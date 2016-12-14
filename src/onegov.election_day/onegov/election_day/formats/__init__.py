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
    __slots__ = ['line', 'error']

    def __init__(self, error, line=None):
        self.error = error
        self.line = line


def load_csv(file, mimetype, expected_headers):
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
                error = FileImportError(_("Not a valid xls/xlsx file."))
            except NotImplementedError:
                error = FileImportError(
                    _("The xls/xlsx file contains unsupported cells.")
                )
        except XLRDError:
            error = FileImportError(_("Not a valid xls/xlsx file."))
        except NotImplementedError:
            error = FileImportError(
                _("The xls/xlsx file contains unsupported cells.")
            )

    if error:
        return csv, error

    try:
        csv = CSVFile(csvfile, expected_headers=expected_headers)
        list(csv.lines)
    except MissingColumnsError as e:
        error = FileImportError(_("Missing columns: '${cols}'", mapping={
            'cols': ', '.join(e.columns)
        }))
    except AmbiguousColumnsError:
        error = FileImportError(_(
            "Could not find the expected columns, "
            "make sure all required columns exist and that there are no "
            "extra columns."
        ))
    except DuplicateColumnNamesError:
        error = FileImportError(_("Some column names appear twice."))
    except InvalidFormatError:
        error = FileImportError(_("Not a valid csv/xls/xlsx file."))
    except EmptyFileError:
        error = FileImportError(_("The csv/xls/xlsx file is empty."))
    except EmptyLineInFileError:
        error = FileImportError(_("The file contains an empty line."))

    return csv, error
