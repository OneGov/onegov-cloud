from __future__ import annotations

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
from onegov.election_day.models import Municipality
from re import match
from xsdata_ech.e_ch_0252_1_0 import DomainOfInfluenceType
from xsdata_ech.e_ch_0252_1_0 import DomainOfInfluenceTypeType
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser

from typing import overload
from typing import Any
from typing import IO
from typing import TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Sequence
    from csv import Dialect
    from onegov.core.csv import DefaultCSVFile
    from onegov.core.csv import DefaultRow
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Election
    from onegov.election_day.models import ElectionCompound
    from onegov.election_day.models import Vote
    from onegov.election_day.types import BallotType
    from onegov.election_day.types import DomainOfInfluence
    from onegov.election_day.types import Gender
    from onegov.election_day.types import Status

    ECHImportResultType = tuple[
        list['FileImportError'],
        set[ElectionCompound | Election | Vote],
        set[ElectionCompound | Election | Vote]
    ]

_T = TypeVar('_T')


EXPATS = (
    # These are used by the BFS but not in the official data!
    9170,  # sg
    19010,
    19020,
    19030,
    19040,
    19050,
    19060,
    19070,
    19080,
    19090,
    19100,
    19110,
    19120,
    19130,
    19140,
    19150,
    19160,
    19170,
    19180,
    19190,
    19200,
    19210,
    19220,
    19230,
    19240,
    19250,
    19260,
)


STATI: tuple[Status, ...] = (
    'unknown',
    'interim',
    'final',
)

BALLOT_TYPES: set[BallotType] = {
    'proposal',
    'counter-proposal',
    'tie-breaker'
}


class FileImportError:
    __slots__ = ('filename', 'line', 'error')

    def __init__(
        self,
        error: str,
        line: int | None = None,
        filename: str | None = None
    ):
        self.filename = filename
        self.error = error
        self.line = line

    def __eq__(self, other: object) -> bool:
        def interpolate(text: str) -> str:
            return text.interpolate() if hasattr(text, 'interpolate') else text

        return (
            isinstance(other, self.__class__)
            and self.filename == other.filename
            and interpolate(self.error) == interpolate(other.error)
            and self.line == other.line
        )

    def __hash__(self) -> int:
        return hash((self.__class__, self.filename, self.error, self.line))


def load_csv(
    file: IO[bytes],
    mimetype: str,
    expected_headers: Sequence[str] | None,
    filename: str | None = None,
    dialect: type[Dialect] | Dialect | str | None = None,
    encoding: str | None = None,
    rename_duplicate_column_names: bool = False
) -> tuple[DefaultCSVFile | None, FileImportError | None]:
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
            except OSError:
                error = FileImportError(
                    _('Not a valid xls/xlsx file.'),
                    filename=filename
                )
            except NotImplementedError:
                error = FileImportError(
                    _('The xls/xlsx file contains unsupported cells.'),
                    filename=filename
                )
            except Exception:
                error = FileImportError(
                    _('Not a valid csv/xls/xlsx file.'),
                    filename=filename
                )
        except OSError:
            error = FileImportError(
                _('Not a valid xls/xlsx file.'),
                filename=filename
            )
        except NotImplementedError:
            error = FileImportError(
                _('The xls/xlsx file contains unsupported cells.'),
                filename=filename
            )
        except Exception:
            error = FileImportError(
                _('Not a valid csv/xls/xlsx file.'),
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
                'Could not find the expected columns, '
                'make sure all required columns exist and that there are no '
                'extra columns.'
            ),
            filename=filename
        )
    except DuplicateColumnNamesError:
        error = FileImportError(
            _('Some column names appear twice.'),
            filename=filename
        )
    except InvalidFormatError:
        error = FileImportError(
            _('Not a valid csv/xls/xlsx file.'),
            filename=filename
        )
    except EmptyFileError:
        error = FileImportError(
            _('The csv/xls/xlsx file is empty.'),
            filename=filename
        )
    except EmptyLineInFileError:
        error = FileImportError(
            _('The file contains an empty line.'),
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
            _('Not a valid csv/xls/xlsx file.'),
            filename=filename
        )

    return csv, error


def load_xml(
    file: IO[bytes]
) -> tuple[Any, None] | tuple[None, FileImportError]:
    """ Loads the given eCH file and returns it as an object.

    :return: A tuple object tree, FileImportError.

    """
    try:
        parser = XmlParser(context=XmlContext())
        return parser.from_bytes(file.read()), None
    except Exception as exception:
        return None, FileImportError(_(
            'Not a valid eCH xml file: ${error}',
            mapping={'error': exception}
        ))


def get_entity_and_district(
    entity_id: int,
    entities: dict[int, dict[str, str]],
    election_or_vote: Election | Vote,
    principal: Canton | Municipality,
    errors: list[str] | None = None
) -> tuple[str, str, str]:
    """ Returns the entity name and district or region (from our static data,
    depending on the domain of the election). Adds optionally an error, if the
    district or region is not part of this election or vote.

    """

    if entity_id == 0:
        return '', '', ''

    entity = entities.get(entity_id, {})
    name = entity.get('name', '')
    district = entity.get('district', '')
    if election_or_vote.domain == 'region':
        district = entity.get('region', '')
    superregion = entity.get('superregion', '')

    if errors is not None:
        if election_or_vote.domain == 'municipality':
            if election_or_vote.domain_segment != name:
                if principal.domain != 'municipality':
                    errors.append(_(
                        '${name} is not part of this business',
                        mapping={
                            'name': entity_id,
                            'district': election_or_vote.domain_segment
                        }
                    ))
        if election_or_vote.domain in ('region', 'district'):
            if election_or_vote.domain_segment != district:
                errors.append(_(
                    '${name} is not part of ${district}',
                    mapping={
                        'name': entity_id,
                        'district': election_or_vote.domain_segment
                    }
                ))

    return name, district, superregion


def line_is_relevant(
    line: DefaultRow,
    number: str,
    district: str | None = None
) -> bool:
    if district:
        return line.sortwahlkreis == district and line.sortgeschaeft == number
    return line.sortgeschaeft == number


@overload
def validate_integer(
    line: DefaultRow,
    col: str,
    treat_none_as_default: bool = True,
    default: int = 0,
    optional: bool = False
) -> int: ...


@overload
def validate_integer(
    line: DefaultRow,
    col: str,
    treat_none_as_default: bool,
    default: _T,
    optional: bool = False
) -> int | _T: ...


@overload
def validate_integer(
    line: DefaultRow,
    col: str,
    treat_none_as_default: bool = True,
    *,
    default: _T,
    optional: bool = False
) -> int | _T: ...


def validate_integer(
    line: DefaultRow,
    col: str,
    treat_none_as_default: bool = True,
    default: int | _T = 0,
    optional: bool = False
) -> int | _T:
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
    except ValueError as exception:
        raise ValueError(_('Invalid integer: ${col}',
                           mapping={'col': col})) from exception


@overload
def validate_numeric(
    line: DefaultRow,
    col: str,
    precision: int,
    scale: int,
    treat_none_as_default: bool = True,
    default: Decimal = Decimal(0),
    optional: bool = False
) -> Decimal: ...


@overload
def validate_numeric(
    line: DefaultRow,
    col: str,
    precision: int,
    scale: int,
    treat_none_as_default: bool,
    default: _T,
    optional: bool = False
) -> Decimal | _T: ...


@overload
def validate_numeric(
    line: DefaultRow,
    col: str,
    precision: int,
    scale: int,
    treat_none_as_default: bool = True,
    *,
    default: _T,
    optional: bool = False
) -> Decimal | _T: ...


def validate_numeric(
    line: DefaultRow,
    col: str,
    precision: int,
    scale: int,
    treat_none_as_default: bool = True,
    default: Decimal | _T = Decimal(0),
    optional: bool = False
) -> Decimal | _T:
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
    except Exception as exception:
        raise ValueError(_('Invalid decimal number: ${col}',
                           mapping={'col': col})) from exception


@overload
def validate_list_id(
    line: DefaultRow,
    col: str,
    treat_empty_as_default: bool = True,
    default: str = '0'
) -> str: ...


@overload
def validate_list_id(
    line: DefaultRow,
    col: str,
    treat_empty_as_default: bool,
    default: _T
) -> str | _T: ...


@overload
def validate_list_id(
    line: DefaultRow,
    col: str,
    treat_empty_as_default: bool = True,
    *,
    default: _T
) -> str | _T: ...


def validate_list_id(
    line: DefaultRow,
    col: str,
    treat_empty_as_default: bool = True,
    default: str | _T = '0'
) -> str | _T:
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


def validate_gender(line: DefaultRow) -> Gender | None:
    result = getattr(line, 'candidate_gender', None) or None
    if result not in (None, 'male', 'female', 'undetermined'):
        raise ValueError(
            _('Invalid gender: ${value}', mapping={'value': result})
        )
    return result


def validate_color(line: DefaultRow, col: str) -> str:
    result = getattr(line, col, '') or ''
    if result and not match(r'^#[0-9A-Fa-f]{6}$', result):
        raise ValueError(
            _('Invalid color: ${col}', mapping={'col': col})
        )
    return result


def convert_ech_domain(
    domain: DomainOfInfluenceType,
    principal: Canton | Municipality,
    entities: dict[int, dict[str, str]],
) -> tuple[bool, DomainOfInfluence, str]:
    """ Convert the given eCH domain to our internal domain and domain
    segment.

    Return True as first argument, if the domain is supported for the given
    principal.

    """
    if domain.domain_of_influence_type == DomainOfInfluenceTypeType.CH:
        return True, 'federation', ''
    if domain.domain_of_influence_type == DomainOfInfluenceTypeType.CT:
        return True, 'canton', ''
    if domain.domain_of_influence_type == DomainOfInfluenceTypeType.BZ:
        # BZ might refer to different domains. This might be for example
        # DomainOfInfluenceMixin.region, DomainOfInfluenceMixin.district
        # or even a different domain we don't know (yet) - such as a court
        # district. Even if we know the district in case of "region" and
        # "district", we don't know the indentifiation, as this is not (yet)
        # standardized at this time.
        # We therefore set the domain to "none" and rely on all the results
        # (one for each municipality) being present, even if not counted yet.
        return True, 'none', ''
    if domain.domain_of_influence_type == DomainOfInfluenceTypeType.MU:
        if isinstance(principal, Municipality):
            return True, 'municipality', ''
        assert domain.domain_of_influence_identification is not None
        name = entities.get(
            int(domain.domain_of_influence_identification), {}
        ).get('name', '')
        return True, 'municipality', name
    if domain.domain_of_influence_type == DomainOfInfluenceTypeType.AN:
        return True, 'none', ''

    return False, 'none', ''
