from decimal import Decimal
from onegov.core.csv import convert_excel_to_csv
from onegov.core.csv import CSVFile
from onegov.core.errors import AmbiguousColumnsError
from onegov.core.errors import DuplicateColumnNamesError
from onegov.core.errors import EmptyFileError
from onegov.core.errors import EmptyLineInFileError
from onegov.core.errors import InvalidFormatError
from onegov.core.errors import MissingColumnsError
from onegov.election_day import _
from re import match


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


class FileImportError:
    __slots__ = ['filename', 'line', 'error']

    def __init__(self, error, line=None, filename=None):
        self.filename = filename
        self.error = error
        self.line = line

    def __eq__(self, other):
        def interpolate(text):
            return text.interpolate() if hasattr(text, 'interpolate') else text

        return (
            self.filename == other.filename
            and interpolate(self.error) == interpolate(other.error)
            and self.line == other.line
        )


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
    if mimetype not in ('text/plain', 'text/csv'):
        try:
            csvfile = convert_excel_to_csv(file, 'Resultate')
            dialect = 'excel'
        except KeyError:
            try:
                csvfile = convert_excel_to_csv(file)
                dialect = 'excel'
            except IOError:
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
        except IOError:
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
    except IndexError as e:
        # Will happen if something goes wrong in src/onegov/core/csv.py:188
        # use list(csv.lines_to_debug) and see which index ix fails
        error = FileImportError(
            e.args[0],
            filename=filename
        )
    except Exception:
        error = FileImportError(
            _("Not a valid csv/xls/xlsx file."),
            filename=filename
        )

    return csv, error


def get_entity_and_district(
    entity_id, entities, election, principal, errors=None
):
    """ Returns the entity name and district or region (from our static data,
    depending on the domain of the election). Adds optionally an error, if the
    district or region is not part of this election.

    """

    if entity_id == 0:
        return '', '', ''

    entity = entities.get(entity_id, {})
    name = entity.get('name', '')
    district = entity.get('district', '')
    if election.domain == 'region':
        district = entity.get('region', '')
    superregion = entity.get('superregion', '')

    if errors is not None:
        if election.domain == 'municipality':
            if election.domain_segment != name:
                if principal.domain != 'municipality':
                    errors.append(_(
                        "${name} is not part of this election",
                        mapping={
                            'name': entity_id,
                            'district': election.domain_segment
                        }
                    ))
        if election.domain in ('region', 'district'):
            if election.domain_segment != district:
                errors.append(_(
                    "${name} is not part of ${district}",
                    mapping={
                        'name': entity_id,
                        'district': election.domain_segment
                    }
                ))

    return name, district, superregion


def line_is_relevant(line, number, district=None):
    if district:
        return line.sortwahlkreis == district and line.sortgeschaeft == number
    return line.sortgeschaeft == number


def validate_integer(line, col, treat_none_as_default=True, default=0,
                     optional=False):
    """
    Checks line of a csv file for a valid integer.
    Raises an error if the attribute is not there.

    :param line: line object from csv reader
    :param col: attribute of line object
    :param default: default to return if line.col is None
    :param treat_none_as_default: raises ValueError if line.col is None
    :param optional: return the default, if the col does not exist.
    :return: integer value of line.col
    """

    if not hasattr(line, col) and optional:
        return default

    result = getattr(line, col)
    if not result:
        if treat_none_as_default:
            return default
        raise ValueError(_('Empty value: ${col}', mapping={'col': col}))
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
        raise ValueError(_('Empty value: ${col}', mapping={'col': col}))
    try:
        return float(result)
    except ValueError:
        raise ValueError(_('Invalid float number: ${col}',
                           mapping={'col': col}))


def validate_numeric(line, col, precision, scale, treat_none_as_default=True,
                     default=0, optional=False):
    """
    Checks line of a csv file for a valid numeric number.
    Raises an error if the attribute is not there.

    :param line: line object from csv reader
    :param col: attribute of line object
    :param precision: the precision (number of decimals)
    :param scale: the scale (number of decimals after decimal point)
    :param default: default to return if line.col is None
    :param treat_none_as_default: raises ValueError if line.col is None
    :param optional: return the default, if the col does not exist.
    :return: numeric value of line.col
    """

    if not hasattr(line, col) and optional:
        return default

    result = getattr(line, col)
    if not result:
        if treat_none_as_default:
            return default
        raise ValueError(_('Empty value: ${col}', mapping={'col': col}))
    try:
        value = Decimal(result)
        return Decimal(format(value, f'{precision}.{scale}f'))
    except Exception:
        raise ValueError(_('Invalid decimal number: ${col}',
                           mapping={'col': col}))


def validate_list_id(line, col, treat_empty_as_default=True, default='0'):
    """ Used to validate list_id that can also be alphanumeric.
     Example: 03B.04
     Previously, the list_id was also 0 if it was empty.
     """
    result = getattr(line, col)
    if result:
        if match(r'^[A-Za-z0-9_\.]+$', result):
            return result
        raise ValueError(
            _('Not an alphanumeric: ${col}', mapping={'col': col})
        )
    elif treat_empty_as_default:
        return default
    raise ValueError(_('Empty value: ${col}', mapping={'col': col}))


def validate_gender(line):
    result = getattr(line, 'candidate_gender', None) or None
    if result not in (None, 'male', 'female', 'undetermined'):
        raise ValueError(
            _('Invalid gender: ${value}', mapping={'value': result})
        )
    return result


def validate_color(line, col):
    result = getattr(line, col, '') or ''
    if result and not match(r'^#[0-9A-Fa-f]{6}$', result):
        raise ValueError(
            _('Invalid color: ${col}', mapping={'col': col})
        )
    return result
