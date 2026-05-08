from __future__ import annotations

import pytest

from datetime import datetime
from decimal import Decimal
from onegov.core.custom import json


class Point:

    def __init__(self, x: int, y: int) -> None:
        self.x = x
        self.y = y

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Point)
            and self.x == other.x and self.y == other.y
        )


def test_custom_json() -> None:

    dt = datetime(2015, 6, 25, 12, 0)

    data = {
        'datetime': dt,
        'date': dt.date(),
        'time': dt.time(),
        'generator': (Decimal(x) for x in range(0, 2)),
        'decimal': Decimal('3.1415926')
    }

    text = json.dumps(data)

    assert '__time__@12:00:00' in text
    assert '__date__@2015-06-25' in text
    assert '__datetime__@2015-06-25T12:00:00' in text
    assert '__decimal__@3.1415926' in text
    assert '["__decimal__@0","__decimal__@1"]' in text

    data['generator'] = [Decimal(x) for x in range(0, 2)]
    assert json.loads(text) == data


def test_not_serializable() -> None:
    with pytest.raises(TypeError):
        json.dumps({'x': object()})


def test_sort_keys() -> None:
    data = {'c': 1, 'a': 2}
    assert json.dumps(data, sort_keys=True) == '{"a":2,"c":1}'


def test_ensure_ascii() -> None:
    assert json.dumps('ä') == '"ä"'
    assert json.dumps('ä', ensure_ascii=True) == '"\\u00e4"'


def test_prefix_serializer() -> None:
    prefix = json.PrefixSerializer(
        target=str,
        prefix='upper',
        encode=lambda s: s.upper(),
        decode=lambda s: s.lower()
    )

    assert prefix.encode('test') == '__upper__@TEST'
    assert prefix.decode('__upper__@TEST') == 'test'


def test_dictionary_serializer() -> None:

    d = json.DictionarySerializer(
        target=Point,
        keys=('x', 'y')
    )

    assert d.encode(Point(1, 2)) == {'x': 1, 'y': 2}
    assert d.decode({'x': 1, 'y': 2}) == Point(1, 2)

    with pytest.raises(TypeError):
        d.decode({'x': 1, 'y': 2, 'z': 3})


def test_serializers() -> None:
    serializers = json.Serializers()

    serializers.register(json.PrefixSerializer(
        target=str,
        prefix='upper',
        encode=lambda s: s.upper(),
        decode=lambda s: s.lower()
    ))

    serializers.register(json.DictionarySerializer(
        target=Point,
        keys=('x', 'y')
    ))

    assert serializers.encode('asdf') == '__upper__@ASDF'
    assert serializers.encode(Point(1, 2)) == {'x': 1, 'y': 2}
    assert serializers.decode('ASDF') == 'ASDF'
    assert serializers.decode('__upper__@ASDF') == 'asdf'
    assert serializers.decode({'x': 1, 'y': 2}) == Point(1, 2)
    assert serializers.decode({'x': 1, 'y': 2, 'z': 3}) == {
        'x': 1,
        'y': 2,
        'z': 3
    }


def test_serializable() -> None:
    serializers = json.Serializers()

    class SerializablePoint(Point, json.Serializable, keys=('x', 'y')):

        @classmethod
        def serializers(cls) -> json.Serializers:
            return serializers  # for testing

    assert serializers.encode(SerializablePoint(1, 2)) == {'x': 1, 'y': 2}
