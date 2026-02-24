""" Sigh. Here we go again, *another* json implementation with support for:

- date
- datetime
- time

Because nobody else does all of these. And if they do (like standardjson), they
don't support decoding...

"""
from __future__ import annotations

import datetime
import isodate
import json
import orjson
import re
import types

from decimal import Decimal
from itertools import chain
from onegov.core.cache.instance_cache import instance_lru_cache


from typing import (
    overload,
    Any,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
    TypeAlias,
    TYPE_CHECKING,
)
if TYPE_CHECKING:
    from _typeshed import SupportsRead, SupportsWrite
    from collections.abc import Callable, Collection, Iterator, Iterable

    from onegov.core.types import JSON_ro, JSONObject_ro

    AnySerializer: TypeAlias = (
        'PrefixSerializer[_T] | DictionarySerializer[_T]')

_T = TypeVar('_T')
_ST = TypeVar('_ST', bound='JSON_ro')


class Serializer(Generic[_T, _ST]):
    """ Provides a way to encode all objects of a given class or its
    subclasses to and from json.

    """

    def __init__(self, target: type[_T]):
        assert isinstance(target, type), 'expects a class'
        self.target = target

    def encode(self, obj: _T) -> _ST:
        raise NotImplementedError

    def decode(self, value: _ST) -> _T:
        raise NotImplementedError


class PrefixSerializer(Serializer[_T, str]):
    """ Serializes objects to a string with a prefix.

    Resulting json values take the form of __prefix__@<value>, where <value>
    is the encoded value and __prefix__@ is the prefix that is used to
    differentiate between normal strings and encoded strings.

    Note that the part after the prefix is user-supplied and possibly unsafe.
    So something like an 'eval' should be out of the question!

    """

    prefix_format = '__{}__@{}'
    prefix_expression = re.compile(r'__(?P<prefix>[a-zA-Z]+)__@')
    prefix_characters = re.compile(r'[a-zA-Z-]+')

    def __init__(
        self,
        target: type[_T],
        prefix: str,
        encode: Callable[[_T], str],
        decode: Callable[[str], _T],
    ):
        super().__init__(target)

        assert self.prefix_characters.match(prefix)

        self.prefix = prefix
        self.prefix_length = len(self.prefix_format.format(prefix, ''))
        self._encode = encode
        self._decode = decode

    def encode(self, obj: _T) -> str:
        return '__{}__@{}'.format(self.prefix, self._encode(obj))

    def decode(self, string: str) -> _T:
        return self._decode(string[self.prefix_length:])


class DictionarySerializer(Serializer[_T, 'JSONObject_ro']):
    """ Serialises objects that can be built with keyword arguments.

    For example::

        class Point:

            def __init__(self, x, y):
                self.x = x
                self.y = y

    Can be serialised using::

        DictionarySerializer(Point, ('x', 'y'))

    Which results in something like this in JSON::

        {'x': 1, 'y': 2}

    As the internal __dict__ represenation is of no concern, __slots__ may
    be used:

        class Point:

            __slots__ = ('x', 'y')

            def __init__(self, x, y):
                self.x = x
                self.y = y

    """

    def __init__(self, target: type[_T], keys: Iterable[str]):
        super().__init__(target)

        self.keys = frozenset(keys)

    def encode(self, obj: _T) -> JSONObject_ro:
        return {k: getattr(obj, k) for k in self.keys}

    def decode(self, dictionary: JSONObject_ro) -> _T:
        return self.target(**dictionary)


class Serializers:
    """ Organises the different serializer implementations under a unifiying
    interface. This allows the actual encoder/decoder to call a single class
    without having to worry how the various serializers need to be looked up
    and called.

    """

    by_prefix: dict[str, PrefixSerializer[Any]]
    by_keys: dict[frozenset[str], DictionarySerializer[Any]]
    known_key_lengths: set[int]

    def __init__(self) -> None:
        self.by_prefix = {}
        self.by_keys = {}
        self.known_key_lengths = set()

    @property
    def registered(self) -> Iterator[AnySerializer[Any]]:
        return chain(self.by_prefix.values(), self.by_keys.values())

    def register(
        self,
        serializer: PrefixSerializer[Any] | DictionarySerializer[Any]
    ) -> None:
        if isinstance(serializer, PrefixSerializer):
            self.by_prefix[serializer.prefix] = serializer

        elif isinstance(serializer, DictionarySerializer):
            self.by_keys[serializer.keys] = serializer
            self.known_key_lengths.add(len(serializer.keys))

        else:
            raise NotImplementedError

    def serializer_for(
        self,
        value: object
    ) -> AnySerializer[Any] | None:
        if isinstance(value, str):
            return self.serializer_for_string(value)

        if isinstance(value, dict):
            return self.serializer_for_dict(value)

        if isinstance(value, type):
            return self.serializer_for_class(value)

        return None

    def serializer_for_string(
        self,
        string: str
    ) -> PrefixSerializer[Any] | None:
        match = PrefixSerializer.prefix_expression.match(string)
        if match is None:
            return None
        return self.by_prefix.get(match.group('prefix'))

    def serializer_for_dict(
        self,
        dictionary: dict[str, Any]
    ) -> DictionarySerializer[Any] | None:

        # we can exit early for all dictionaries which cannot possibly match
        # the keys we're looking for by comparing the number of keys in the
        # dictionary - this is much cheaper than the next lookup
        if len(dictionary.keys()) not in self.known_key_lengths:
            return None

        return self.by_keys.get(frozenset(dictionary.keys()))

    @instance_lru_cache(maxsize=16)
    def serializer_for_class(
        self,
        cls: type[_T]
    ) -> AnySerializer[_T] | None:
        matches = (s for s in self.registered if issubclass(cls, s.target))
        return next(matches, None)

    def encode(self, value: object) -> JSON_ro:
        serializer = self.serializer_for_class(value.__class__)

        if serializer:
            return serializer.encode(value)

        # NOTE: orjson will not natively detect tuple subclasses
        #       like namedtuple/NamedTuple, so we need to check
        #       for it here if we want feature parity, we could
        #       also decide to serialize NamedTuple and dataclasses
        #       as dictionaries in the future.
        if isinstance(value, (tuple, types.GeneratorType)):
            return list(value)

        raise TypeError('{} is not JSON serializable'.format(repr(value)))

    def decode(self, value: Any) -> Any:
        serializer = self.serializer_for(value)

        if serializer:
            value = serializer.decode(value)
        elif isinstance(value, dict):
            for k, v in value.items():
                value[k] = self.decode(v)
        elif isinstance(value, list):
            for idx, v in enumerate(value):
                value[idx] = self.decode(v)

        return value


# The builtin serializers
# FIXME: is the aim of these serializers to be fast, or should the
#        output be human readable? If it's the former, then we should
#        probably change some of these serializers, the iso format
#        is not very efficient in deserialization, a pair with a
#        timestamp and the timezone would be much faster
default_serializers = Serializers()

default_serializers.register(PrefixSerializer(
    prefix='datetime',
    target=datetime.datetime,
    encode=isodate.datetime_isoformat,
    decode=isodate.parse_datetime
))

default_serializers.register(PrefixSerializer(
    prefix='time',
    target=datetime.time,
    encode=isodate.time_isoformat,
    decode=isodate.parse_time
))

default_serializers.register(PrefixSerializer(
    prefix='date',
    target=datetime.date,
    encode=isodate.date_isoformat,
    decode=isodate.parse_date
))

default_serializers.register(PrefixSerializer(
    prefix='decimal',
    target=Decimal,
    encode=str,
    decode=Decimal
))


class Serializable:
    """ Classes inheriting from this base are serialised using the
    :class:`DictionarySerializer` class.

    The keys that should be used need to be specified as follows::

        class Point(Serializable, keys=('x', 'y')):

            def __init__(self, x, y):
                self.x = x
                self.y = y

    """

    serialized_keys: ClassVar[Collection[str]]

    @classmethod
    def serializers(cls) -> Serializers:
        return default_serializers  # for testing

    def __init_subclass__(cls, keys: Collection[str], **kwargs: Any):
        super().__init_subclass__(**kwargs)

        cls.serialized_keys = keys
        cls.serializers().register(DictionarySerializer(
            target=cls,
            keys=keys
        ))


DEFAULT_DUMPS_OPTIONS = (
    orjson.OPT_PASSTHROUGH_DATACLASS
    | orjson.OPT_PASSTHROUGH_DATETIME
)


@overload
def dumps(
    obj: None,
    *,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    indent: Literal[2] | None = None,
) -> None: ...
@overload
def dumps(
    obj: Any,
    *,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    indent: Literal[2] | None = None,
) -> str: ...


def dumps(
    obj: Any | None,
    *,
    ensure_ascii: bool = False,
    sort_keys: bool = False,
    indent: Literal[2] | None = None,
) -> str | None:

    if obj is not None:
        if ensure_ascii:
            # NOTE: We sometimes dump json to headers for intercooler
            #       in which case we need to ensure ascii, which we
            #       can only do with stdlib's json.dumps
            return json.dumps(
                obj,
                default=default_serializers.encode,
                separators=(',', ':'),
                ensure_ascii=True,
                indent=indent,
                sort_keys=sort_keys,
            )
        return dumps_bytes(
            obj,
            sort_keys=sort_keys,
            indent=indent,
        ).decode('utf-8')
    return None


def dumps_bytes(
    obj: Any,
    *,
    sort_keys: bool = False,
    indent: Literal[2] | None = None,
) -> bytes:

    options = DEFAULT_DUMPS_OPTIONS

    if sort_keys:
        options |= orjson.OPT_SORT_KEYS

    if indent:
        assert indent == 2
        options |= orjson.OPT_INDENT_2

    return orjson.dumps(
        obj,
        default=default_serializers.encode,
        option=options
    )


def loads(txt: str | bytes | bytearray | memoryview | None) -> Any:
    if txt is not None:
        return default_serializers.decode(orjson.loads(txt))

    return {}


def dump(
    data: Any,
    fp: SupportsWrite[str],
    *,
    sort_keys: bool = False,
    indent: Literal[2] | None = None,
) -> None:
    fp.write(dumps(data, sort_keys=sort_keys, indent=indent))


def dump_bytes(
    data: Any,
    fp: SupportsWrite[bytes],
    *,
    sort_keys: bool = False,
    indent: Literal[2] | None = None,
) -> None:
    fp.write(dumps_bytes(data, sort_keys=sort_keys, indent=indent))


def load(fp: SupportsRead[str | bytes]) -> Any:
    return loads(fp.read())
