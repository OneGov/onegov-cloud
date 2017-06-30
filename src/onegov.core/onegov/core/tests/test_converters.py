from datetime import date, datetime
from onegov.core.converters import extended_date_converter
from onegov.core.converters import datetime_converter
from onegov.core.converters import uuid_converter
from uuid import UUID


def test_date_converter():
    converter = extended_date_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']
    assert converter.encode(date(2008, 12, 30)) == ['2008-12-30']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None
    assert converter.decode(['2008-12-30']) == date(2008, 12, 30)


def test_datetime_converter():
    converter = datetime_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']
    assert converter.encode(datetime(2008, 12, 30)) == ['2008-12-30T00:00:00']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None
    assert converter.decode(['2008-12-30T12:34:56']) == datetime(
        2008, 12, 30, 12, 34, 56)


def test_uuid_converter():
    converter = uuid_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']
    assert converter.encode(UUID('930a8bf4-e532-4b39-bf64-bd05e81acf01')) == \
        ['930a8bf4e5324b39bf64bd05e81acf01']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None
    assert converter.decode(['930a8bf4-e532-4b39-bf64-bd05e81acf01']) == \
        UUID('930a8bf4e5324b39bf64bd05e81acf01')
