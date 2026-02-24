""" Contains custom converters. """
from __future__ import annotations

import isodate
import morepath

from datetime import date, datetime
from onegov.core.framework import Framework
from onegov.core.orm.abstract import MoveDirection
from onegov.core.utils import is_uuid
from onegov.core.custom import custom_json as json
from time import mktime, strptime
from uuid import UUID


from typing import get_args, get_origin, overload, Any, Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Mapping
    from typing import LiteralString


@overload
def extended_date_decode(s: Literal['']) -> None: ...  # type:ignore
@overload
def extended_date_decode(s: str) -> date: ...


def extended_date_decode(s: str) -> date | None:
    """ Decodes a date string HTML5 (RFC3339) compliant."""
    if not s:
        return None

    try:
        return date.fromtimestamp(mktime(strptime(s, '%Y-%m-%d')))
    except OverflowError as exception:
        raise ValueError() from exception


def extended_date_encode(d: date | None) -> str:
    """ Encodes a date HTML5 (RFC3339) compliant. """
    if not d:
        return ''

    return d.strftime('%Y-%m-%d')


extended_date_converter = morepath.Converter(
    decode=extended_date_decode, encode=extended_date_encode
)


@overload
def json_decode(s: Literal['']) -> None: ...  # type:ignore[overload-overlap]
@overload
def json_decode(s: str) -> dict[str, Any]: ...


# NOTE: Technically this is incorrect, but we assume, we only ever
#       decode a JSON object, and not JSON in general
def json_decode(s: str) -> dict[str, Any] | None:
    """ Decodes a json string to a dict. """
    if not s:
        return None

    return json.loads(s)


def json_encode(d: Mapping[str, Any] | None) -> str:
    """ Encodes a dictionary to json. """
    if not d:
        return '{}'

    return json.dumps(d)


json_converter = morepath.Converter(
    decode=json_decode, encode=json_encode
)


def uuid_decode(s: str) -> UUID | None:
    """ Turns a uuid string into a UUID instance. """

    return is_uuid(s) and UUID(s) or None


def uuid_encode(uuid: UUID | str | None) -> str:
    """ Turns a UUID instance into a uuid string. """
    if not uuid:
        return ''

    if isinstance(uuid, str):
        return uuid

    return uuid.hex


uuid_converter = morepath.Converter(
    decode=uuid_decode, encode=uuid_encode
)


@Framework.converter(type=UUID)
def get_default_uuid_converter() -> morepath.Converter[UUID]:
    return uuid_converter


@overload
def bool_decode(s: Literal['0', '']) -> Literal[False]: ...
@overload
def bool_decode(s: Literal['1']) -> Literal[True]: ...
@overload
def bool_decode(s: str) -> bool: ...


def bool_decode(s: str) -> bool:
    """ Decodes a boolean. """
    return not (s == '0' or s == '')


@overload
def bool_encode(d: Literal[False] | None) -> Literal['0']: ...
@overload
def bool_encode(d: Literal[True]) -> Literal['1']: ...
@overload
def bool_encode(d: bool | None) -> Literal['0', '1']: ...


def bool_encode(d: bool | None) -> Literal['0', '1']:
    """ Encodes a boolean. """
    return d and '1' or '0'


bool_converter: morepath.Converter[bool] = morepath.Converter(
    decode=bool_decode, encode=bool_encode
)


@Framework.converter(type=bool)
def get_default_bool_converter() -> morepath.Converter[bool]:
    return bool_converter


@overload
def datetime_decode(s: Literal['']) -> None: ...  # type:ignore
@overload
def datetime_decode(s: str) -> datetime: ...


def datetime_decode(s: str) -> datetime | None:
    """ Decodes a datetime. """
    return None if not s else isodate.parse_datetime(s)


def datetime_encode(d: datetime | None) -> str:
    """ Encodes a datetime. """
    return isodate.datetime_isoformat(d) if d else ''


datetime_converter = morepath.Converter(
    decode=datetime_decode, encode=datetime_encode
)


def datetime_year_decode(s: str) -> int:
    """ Decodes a year limited to the range datetime provides. """
    year = int(s)
    if datetime.min.year <= year <= datetime.max.year:
        return year
    raise ValueError('year outside valid range')


def datetime_year_encode(y: int | None) -> str:
    """ Encodes a year. """
    return str(y) if y is not None else ''


datetime_year_converter = morepath.Converter(
    decode=datetime_year_decode, encode=datetime_year_encode
)


@Framework.converter(type=datetime)
def get_default_datetime_converter() -> morepath.Converter[datetime]:
    return datetime_converter


def integer_range_decode(s: str) -> tuple[int, int] | None:
    if not s:
        return None
    s, _, e = s.partition('-')
    return int(s), int(e)


def integer_range_encode(t: tuple[int, int] | None) -> str:
    return t and f'{t[0]}-{t[1]}' or ''


integer_range_converter = morepath.Converter(
    decode=integer_range_decode, encode=integer_range_encode
)


def move_direction_decode(s: str) -> MoveDirection | None:
    try:
        return MoveDirection[s]
    except KeyError:
        return None


# we are slightly more lax and allow arbitrary str values when encoding
# so we can provide e.g. a template string that gets replaced later on
def move_direction_encode(d: str | MoveDirection | None) -> str:
    if d is None:
        return ''
    elif isinstance(d, str):
        return d
    return d.name


move_direction_converter = morepath.Converter(
    decode=move_direction_decode, encode=move_direction_encode
)


@Framework.converter(type=MoveDirection)
def get_default_move_direction_converter(
) -> morepath.Converter[MoveDirection]:
    return move_direction_converter


if TYPE_CHECKING:
    LiteralConverterBase = morepath.Converter[LiteralString]
else:
    LiteralConverterBase = morepath.Converter


class LiteralConverter(LiteralConverterBase):
    """ This is a ``Converter`` counter-part to ``typing.Literal``.
    """

    # TODO: This should use TypeForm eventually
    @overload
    def __init__(self, literal_type: Any, /) -> None: ...

    @overload
    def __init__(self, *literals: LiteralString) -> None: ...

    def __init__(self, *literals: Any) -> None:
        if len(literals) == 1 and get_origin(literals[0]) is Literal:
            literals = get_args(literals[0])

        if not all(isinstance(v, str) for v in literals):
            # TODO: Consider supporting float/int literals via their
            #       respective converters in the future
            raise ValueError('We only support string literals for simplicity')

        self.allowed_values: set[str] = set(literals)

    def single_decode(self, string: str) -> str | None:
        return string if string in self.allowed_values else None

    def single_encode(self, value: str | None) -> str:
        # NOTE: If we ever support non-string literals we may need to actually
        #       encode them here.
        return str(value) if value is not None else ''
