from __future__ import annotations

import pytest
from datetime import date, datetime
from onegov.core.converters import extended_date_converter
from onegov.core.converters import datetime_converter
from onegov.core.converters import uuid_converter
from onegov.core.converters import LiteralConverter
from typing import Literal
from uuid import UUID


def test_date_converter() -> None:
    converter = extended_date_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']  # type: ignore[arg-type]
    assert converter.encode(date(2008, 12, 30)) == ['2008-12-30']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None  # type: ignore[list-item]
    assert converter.decode(['2008-12-30']) == date(2008, 12, 30)


def test_datetime_converter() -> None:
    converter = datetime_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']  # type: ignore[arg-type]
    assert converter.encode(datetime(2008, 12, 30)) == ['2008-12-30T00:00:00']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None  # type: ignore[list-item]
    assert converter.decode(['2008-12-30T12:34:56']) == datetime(
        2008, 12, 30, 12, 34, 56)


def test_uuid_converter() -> None:
    converter = uuid_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']  # type: ignore[arg-type]
    assert converter.encode(UUID('930a8bf4-e532-4b39-bf64-bd05e81acf01')) == [
    '930a8bf4e5324b39bf64bd05e81acf01']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None  # type: ignore[list-item]
    assert converter.decode(['930a8bf4-e532-4b39-bf64-bd05e81acf01']) == UUID(
        '930a8bf4e5324b39bf64bd05e81acf01')


def test_literal_converter() -> None:
    converter = LiteralConverter(Literal['asc', 'desc'])
    assert converter.allowed_values == {'asc', 'desc'}
    assert converter.encode(None) == ['']
    # NOTE: we allow bogus values to be encoded so we can e.g. build
    #       url patterns, we only filter values on decode
    assert converter.encode('bogus') == ['bogus']
    assert converter.encode(1) == ['1']  # type: ignore[arg-type]

    assert converter.decode(['']) is None
    assert converter.decode(['bogus']) is None
    assert converter.decode(['asc']) == 'asc'
    assert converter.decode(['desc']) == 'desc'

    with pytest.raises(ValueError):
        LiteralConverter(Literal[0, 1])

    converter2 = LiteralConverter('asc', 'desc')
    assert converter2.allowed_values == converter2.allowed_values
