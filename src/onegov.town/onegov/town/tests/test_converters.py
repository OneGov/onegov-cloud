from datetime import date
from onegov.town.converters import extended_date_converter


def test_converters():
    converter = extended_date_converter

    assert converter.encode(None) == ['']
    assert converter.encode('') == ['']
    assert converter.encode(date(2008, 12, 30)) == ['2008-12-30']

    assert converter.decode(['']) is None
    assert converter.decode([None]) is None
    assert converter.decode(['2008-12-30']) == date(2008, 12, 30)
