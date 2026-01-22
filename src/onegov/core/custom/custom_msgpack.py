from __future__ import annotations

import datetime
import isodate
import ormsgpack

from decimal import Decimal
from markupsafe import Markup
from sqlalchemy.engine.result import result_tuple  # type: ignore[attr-defined]
from sqlalchemy.engine.row import Row  # type: ignore[import-untyped]
from types import GeneratorType
from uuid import UUID


from typing import Any, ClassVar, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Collection, Iterable

_T = TypeVar('_T')
_TypeT = TypeVar('_TypeT', bound=type[object])


class Serializer(Generic[_T]):
    """ Provides a way to encode all objects of a given class or its
    subclasses to and from MessagePack using extension types.

    """

    def __init__(self, tag: int, target: type[_T]):
        assert isinstance(target, type), 'expects a class'
        assert 0 <= tag <= 127, 'needs to be between 0 and 127'
        self.tag = tag
        self.target = target

    def encode(self, obj: _T) -> bytes:
        raise NotImplementedError

    def decode(self, value: bytes) -> _T:
        raise NotImplementedError


class BytesSerializer(Serializer[_T]):
    """ Serializes objects to a byte string. """

    def __init__(
        self,
        tag: int,
        target: type[_T],
        encode: Callable[[_T], bytes],
        decode: Callable[[bytes], _T],
    ):
        super().__init__(tag, target)

        self._encode = encode
        self._decode = decode

    def encode(self, obj: _T) -> bytes:
        return self._encode(obj)

    def decode(self, value: bytes) -> _T:
        return self._decode(value)


class StringSerializer(Serializer[_T]):
    """ Serializes objects to a string. """

    def __init__(
        self,
        tag: int,
        target: type[_T],
        encode: Callable[[_T], str],
        decode: Callable[[str], _T],
    ):
        super().__init__(tag, target)

        self._encode = encode
        self._decode = decode

    def encode(self, obj: _T) -> bytes:
        return self._encode(obj).encode('utf-8')

    def decode(self, value: bytes) -> _T:
        return self._decode(value.decode('utf-8'))


class DictionarySerializer(Serializer[_T]):
    """ Serializes objects that can be built with keyword arguments.

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

    def __init__(self, tag: int, target: type[_T], keys: Iterable[str]):
        super().__init__(tag, target)

        self.keys = keys = tuple(keys)
        assert len(keys) == len(set(keys)), 'duplicate keys given'
        self.constructor = getattr(target, 'from_dict', target)

    def encode(self, obj: _T) -> bytes:
        return packb([getattr(obj, k) for k in self.keys])

    def decode(self, value: bytes) -> _T:
        values = unpackb(value)
        assert isinstance(values, list)
        return self.constructor(**dict(zip(self.keys, values, strict=True)))


class Serializers:
    """ Organises the different serializer implementations under a unifiying
    interface. This allows the actual encoder/decoder to call a single class
    without having to worry how the various serializers need to be looked up
    and called.

    """

    by_tag: dict[int, Serializer[Any]]
    by_type: dict[type[object], tuple[int, Serializer[Any]]]

    def __init__(self) -> None:
        self.by_tag = {}
        self.by_type = {}

    def register(
        self,
        serializer: Serializer[Any]
    ) -> None:

        tag = serializer.tag
        assert tag not in self.by_tag
        self.by_tag[tag] = serializer
        assert serializer.target not in self.by_type
        self.by_type[serializer.target] = (tag, serializer)

    def encode(self, value: object) -> object:
        tag_and_serializer = self.by_type.get(value.__class__)

        if tag_and_serializer is None:
            if isinstance(value, dict):
                return dict(value)
            elif isinstance(value, Row):
                tag_and_serializer = self.by_type[Row]
            elif isinstance(value, GeneratorType):
                tag_and_serializer = self.by_type[tuple]
            else:
                raise TypeError(f'{value!r} is not MessagePack serializable')

        tag, serializer = tag_and_serializer
        return ormsgpack.Ext(tag, serializer.encode(value))

    def decode(self, tag: int, value: bytes) -> Any:
        serializer = self.by_tag.get(tag)

        if serializer is not None:
            value = serializer.decode(value)

        return value


# The builtin serializers
default_serializers = Serializers()

# TODO: More efficient date/time serialization/deserialization
default_serializers.register(StringSerializer(
    tag=0,
    target=datetime.datetime,
    encode=isodate.datetime_isoformat,
    decode=isodate.parse_datetime
))

default_serializers.register(StringSerializer(
    tag=1,
    target=datetime.time,
    encode=isodate.time_isoformat,
    decode=isodate.parse_time
))

default_serializers.register(StringSerializer(
    tag=2,
    target=datetime.date,
    encode=isodate.date_isoformat,
    decode=isodate.parse_date
))

default_serializers.register(StringSerializer(
    tag=3,
    target=Decimal,
    encode=str,
    decode=Decimal
))

default_serializers.register(BytesSerializer(
    tag=4,
    target=UUID,
    encode=lambda u: u.bytes,
    decode=lambda b: UUID(bytes=b)
))

# NOTE: This might not be worth the cost in performance
#       maybe we're fine with tuples turning into lists
#       remove `OPT_PASSTHROUGH_TUPLE` when removing this
default_serializers.register(BytesSerializer(
    tag=5,
    target=tuple,
    encode=lambda t: packb(list(t)),
    decode=lambda b: tuple(unpackb(b))
))

# NOTE: We currently only use this to serialize the groupids
#       for the current identity, we could consider replacing
#       this with a serializer for morepath.Identity instead
default_serializers.register(BytesSerializer(
    tag=6,
    target=frozenset,
    encode=lambda t: packb(list(t)),
    decode=lambda b: frozenset(unpackb(b))
))


# NOTE: SQLAlchemy result support
def store_sqlalchemy_row(r: Row[Any]) -> bytes:
    fields = list(r._fields)
    data = [getattr(r, name) for name in fields]
    return packb([fields, data])


def load_sqlalchemy_row(b: bytes) -> Row[Any]:
    fields, data = unpackb(b)
    cls = result_tuple(fields)
    return cls(data)


default_serializers.register(BytesSerializer(
    tag=7,
    target=Row,
    encode=store_sqlalchemy_row,
    decode=load_sqlalchemy_row
))

default_serializers.register(StringSerializer(
    tag=8,
    target=Markup,
    encode=str,
    decode=Markup
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

    def __init_subclass__(cls, tag: int, keys: Collection[str], **kwargs: Any):
        super().__init_subclass__(**kwargs)

        cls.serialized_keys = keys
        cls.serializers().register(DictionarySerializer(
            tag=tag,
            target=cls,
            keys=keys
        ))


def make_serializable(
    *,
    tag: int,
    serializers: Serializers = default_serializers
) -> Callable[[_TypeT], _TypeT]:

    def decorator(cls: _TypeT) -> _TypeT:
        keys = getattr(cls, '_fields', getattr(cls, '__slots__', ()))
        assert keys, f'{cls!r} is not serializable'
        serializers.register(DictionarySerializer(
            tag=tag,
            target=cls,
            keys=keys
        ))
        return cls

    return decorator


PACK_OPTIONS = (
    # NOTE: Technically we only need this for one instance where we
    #       want `None` as a key, but it should be fine to allow
    #       other types as well. It only allows the basic types
    #       anyways and no Ext types.
    ormsgpack.OPT_NON_STR_KEYS
    # NOTE: We want serialization to be fully reversible
    #       so we use our own serialization for these
    | ormsgpack.OPT_PASSTHROUGH_SUBCLASS
    | ormsgpack.OPT_PASSTHROUGH_DATACLASS
    | ormsgpack.OPT_PASSTHROUGH_DATETIME
    | ormsgpack.OPT_PASSTHROUGH_TUPLE
    | ormsgpack.OPT_PASSTHROUGH_UUID
)


def packb(obj: Any) -> bytes:
    return ormsgpack.packb(
        obj,
        default=default_serializers.encode,
        option=PACK_OPTIONS
    )


def unpackb(value: bytes) -> Any:
    return ormsgpack.unpackb(
        value,
        ext_hook=default_serializers.decode,
        option=ormsgpack.OPT_NON_STR_KEYS,
    )


def packable(obj: Any) -> bool:
    try:
        packb(obj)
    except Exception:
        return False
    else:
        return True
