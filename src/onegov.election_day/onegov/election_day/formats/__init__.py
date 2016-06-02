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

    if mimetype == 'text/plain':
        csvfile = file
    else:
        try:
            csvfile = convert_xls_to_csv(file, 'Resultate')
        except IOError:
            csvfile = convert_xls_to_csv(file)

    try:
        csv = CSVFile(csvfile, expected_headers=expected_headers)
    except MissingColumnsError as e:
        error = FileImportError(_("Missing columns: '${cols}'", mapping={
            'cols': ', '.join(e.columns)
        }))
    except AmbiguousColumnsError as e:
        error = FileImportError(_(
            "Could not find the expected columns, "
            "make sure all required columns exist and that there are no "
            "extra columns."
        ))
    except DuplicateColumnNamesError as e:
        error = FileImportError(_("Some column names appear twice."))
    except InvalidFormatError as e:
        error = FileImportError(_("Not a valid csv/xls/xlsx file."))
    except EmptyFileError as e:
        error = FileImportError(_("The csv/xls/xlsx file is empty."))
    except EmptyLineInFileError as e:
        error = FileImportError(_("The file contains an empty line."))

    return csv, error
