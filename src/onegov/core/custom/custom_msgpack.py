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
import ormsgpack

from decimal import Decimal
from markupsafe import Markup
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

    def __init__(self, target: type[_T]):
        assert isinstance(target, type), 'expects a class'
        self.target = target

    def encode(self, obj: _T) -> bytes:
        raise NotImplementedError

    def decode(self, value: bytes) -> _T:
        raise NotImplementedError


class BytesSerializer(Serializer[_T]):
    """ Serializes objects to a byte string. """

    def __init__(
        self,
        target: type[_T],
        encode: Callable[[_T], bytes],
        decode: Callable[[bytes], _T],
    ):
        super().__init__(target)

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
        target: type[_T],
        encode: Callable[[_T], str],
        decode: Callable[[str], _T],
    ):
        super().__init__(target)

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

    def __init__(self, target: type[_T], keys: Iterable[str]):
        super().__init__(target)

        self.keys = frozenset(keys)

    def encode(self, obj: _T) -> bytes:
        return packb({k: getattr(obj, k) for k in self.keys})

    def decode(self, value: bytes) -> _T:
        return self.target(**unpackb(value))


class Serializers:
    """ Organises the different serializer implementations under a unifiying
    interface. This allows the actual encoder/decoder to call a single class
    without having to worry how the various serializers need to be looked up
    and called.

    """

    by_tag: dict[int, Serializer[Any]]
    by_type: dict[type[object], tuple[int, Serializer[Any]]]

    def __init__(self) -> None:
        self._last_tag = 0
        self.by_tag = {}
        self.by_type = {}

    def register(
        self,
        serializer: Serializer[Any]
    ) -> None:

        tag = self._last_tag
        assert tag <= 127
        assert tag not in self.by_tag
        self.by_tag[tag] = serializer
        assert serializer.target not in self.by_type
        self.by_type[serializer.target] = (tag, serializer)
        self._last_tag += 1

    def encode(self, value: object) -> ormsgpack.Ext:
        tag_and_serializer = self.by_type[value.__class__]

        if tag_and_serializer is None:
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

default_serializers.register(StringSerializer(
    target=datetime.datetime,
    encode=isodate.datetime_isoformat,
    decode=isodate.parse_datetime
))

default_serializers.register(StringSerializer(
    target=datetime.time,
    encode=isodate.time_isoformat,
    decode=isodate.parse_time
))

default_serializers.register(StringSerializer(
    target=datetime.date,
    encode=isodate.date_isoformat,
    decode=isodate.parse_date
))

default_serializers.register(StringSerializer(
    target=Decimal,
    encode=str,
    decode=Decimal
))

default_serializers.register(BytesSerializer(
    target=UUID,
    encode=lambda u: u.bytes,
    decode=lambda b: UUID(bytes=b)
))

# NOTE: This might not be worth the cost in performance
#       maybe we're fine with tuples turning into lists
#       remove `OPT_PASSTHROUGH_TUPLE` when removing this
default_serializers.register(BytesSerializer(
    target=tuple,
    encode=lambda t: packb(list(t)),
    decode=lambda b: tuple(unpackb(b))
))

default_serializers.register(StringSerializer(
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

    def __init_subclass__(cls, keys: Collection[str], **kwargs: Any):
        super().__init_subclass__(**kwargs)

        cls.serialized_keys = keys
        cls.serializers().register(DictionarySerializer(
            target=cls,
            keys=keys
        ))


def make_serializable(cls: _TypeT) -> _TypeT:
    keys = getattr(cls, '_fields', getattr(cls, '__slots__', ()))
    assert keys, f'{cls!r} is not serializable'
    default_serializers.register(DictionarySerializer(
        target=cls,
        keys=keys
    ))
    return cls


PACK_OPTIONS = (
    # NOTE: We want serialization to be fully reversible
    #       so we use our own serialization for these
    ormsgpack.OPT_PASSTHROUGH_SUBCLASS
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
    )
