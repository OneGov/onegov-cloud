from __future__ import annotations

import pytest

from datetime import date, datetime, time, UTC
from decimal import Decimal
from onegov.core.custom import msgpack
from onegov.core.i18n.translation_string import TranslationMarkup
from markupsafe import Markup
from translationstring import TranslationString
from typing import NamedTuple
from uuid import uuid4


class Point:

    __slots__ = ('x', 'y')

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Point)
            and self.x == other.x and self.y == other.y
        )


class PointTuple(NamedTuple):
    x: int
    y: int


def test_custom_msgpack() -> None:

    dt = datetime(2015, 6, 25, 12, 0)

    data = {
        'datetime': dt,
        'date': dt.date(),
        'time': dt.time(),
        'generator': (Decimal(x) for x in range(0, 2)),
        'decimal': Decimal('3.1415926')
    }

    packed = msgpack.packb(data)
    data['generator'] = tuple(Decimal(x) for x in range(0, 2))
    assert msgpack.unpackb(packed) == data


@pytest.mark.parametrize('data', [
    date(2020, 10, 10),
    datetime(2020, 10, 10, 12, 0, 14, 0, UTC),
    time(15, 0, 15),
    uuid4(),
    (Decimal(1), Decimal(2)),
    Markup('<b>safe</b>'),
    TranslationString(
        'Hello ${name}',
        domain='foo',
        context='bar',
        mapping={'name': 'John Doe'}
    ),
    TranslationMarkup(
        'Hello <b>${name}</b>',
        domain='foo',
        context='bar',
        mapping={'name': 'John Doe'}
    ),
    {'a': Decimal(1), None: Decimal(2)}
])
def test_roundtrip(data: object) -> None:
    assert msgpack.unpackb(msgpack.packb(data)) == data


def test_not_serializable() -> None:
    with pytest.raises(TypeError):
        msgpack.packb({'x': object()})


def test_string_serializer() -> None:
    s = msgpack.StringSerializer(
        tag=0,
        target=str,
        encode=lambda s: s.upper(),
        decode=lambda s: s.lower()
    )

    assert s.encode('test') == b'TEST'
    assert s.decode(b'TEST') == 'test'


def test_dictionary_serializer() -> None:

    d = msgpack.DictionarySerializer(
        tag=0,
        target=Point,
        keys=('x', 'y')
    )

    assert d.decode(d.encode(Point(1, 2))) == Point(1, 2)


def test_make_serializable() -> None:
    serializers = msgpack.Serializers()

    msgpack.make_serializable(tag=0, serializers=serializers)(Point)
    msgpack.make_serializable(tag=1, serializers=serializers)(PointTuple)

    tag, s = serializers.by_type[Point]
    assert tag == 0
    b = s.encode(Point(1, 2))
    assert serializers.decode(tag, b) == Point(1, 2)

    tag, s = serializers.by_type[PointTuple]
    assert tag == 1
    b = s.encode(PointTuple(1, 2))
    assert serializers.decode(tag, b) == PointTuple(1, 2)


def test_serializers() -> None:
    serializers = msgpack.Serializers()

    serializers.register(msgpack.StringSerializer(
        tag=0,
        target=str,
        encode=lambda s: s.upper(),
        decode=lambda s: s.lower()
    ))

    serializers.register(msgpack.DictionarySerializer(
        tag=1,
        target=Point,
        keys=('x', 'y')
    ))

    tag, s = serializers.by_type[str]
    assert tag == 0
    assert serializers.decode(tag, s.encode('asdf')) == 'asdf'
    tag, s = serializers.by_type[Point]
    assert tag == 1
    assert serializers.decode(tag, s.encode(Point(1, 2))) == Point(1, 2)


def test_serializable() -> None:
    serializers = msgpack.Serializers()

    class SerializablePoint(
        Point,
        msgpack.Serializable,
        tag=0,
        keys=('x', 'y')
    ):

        @classmethod
        def serializers(cls) -> msgpack.Serializers:
            return serializers  # for testing

    tag, s = serializers.by_type[SerializablePoint]
    assert tag == 0
    b = s.encode(SerializablePoint(1, 2))
    assert serializers.decode(tag, b) == SerializablePoint(1, 2)
