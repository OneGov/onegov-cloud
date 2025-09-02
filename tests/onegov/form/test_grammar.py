from __future__ import annotations

import pytest
import re

from datetime import date as dateobj
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from onegov.form.utils import decimal_range
from onegov.form.parser.grammar import (
    checkbox,
    chip_nr,
    code,
    currency,
    date,
    datetime,
    decimal,
    decimal_range_field,
    email,
    field_identifier,
    fileinput,
    integer_range_field,
    password,
    radio,
    stdnum,
    text_without,
    textarea,
    textfield,
    time,
    url,
    valid_date_range,
    with_whitespace_inside,
    video_url,
)
from pyparsing import ParseFatalException


def test_text_without() -> None:
    assert text_without('?!').parseString('what')[0] == 'what'
    assert text_without('?!').parseString('what what?')[0] == 'what'
    assert text_without('?!').parseString('what!')[0] == 'what'
    assert text_without('?').parseString('what!')[0] == 'what!'


def test_with_whitespace_inside() -> None:
    text = text_without('')
    assert with_whitespace_inside(text).parseString("a b")[0] == "a b"
    assert with_whitespace_inside(text).parseString("a b ")[0] == "a b"
    assert with_whitespace_inside(text).parseString("a  b ")[0] == "a"


def test_field_identifier() -> None:
    parse = field_identifier().parseString

    assert parse("Yes?=").asDict() == {'required': False, 'label': 'Yes?'}
    assert parse("Yes?*=").asDict() == {'required': True, 'label': 'Yes?'}

    assert parse("OMG. U ok?! =").label == "OMG. U ok?!"
    assert parse("a b =").label == "a b"
    assert parse("ab =").label == "ab"
    assert parse("1 = 2").label == "1"
    assert parse("what=").label == "what"
    assert parse("what=*").label == "what"
    assert parse("what*=").label == "what"
    assert parse("What* =").label == 'What'
    assert parse("Sure?! =").label == 'Sure?!'

    assert not parse("Do you?! =").required
    assert not parse("what=*").required
    assert parse("What* =").required
    assert parse("What* =").required
    assert parse("What* =").required


def test_textfield() -> None:

    field = textfield()

    f = field.parseString('___')
    assert f.type == 'text'
    assert not f.length
    assert f.asDict() == {'type': 'text'}

    f = field.parseString('___[25]')
    assert f.type == 'text'
    assert f.length == 25
    assert f.asDict() == {'length': 25, 'type': 'text'}

    # valid regex
    f = field.parseString('___/[0-9]{4}')
    assert f.type == 'text'
    assert not f.length
    assert f.asDict() == {
        'type': 'text',
        'regex': re.compile('[0-9]{4}')
    }

    # invalid regex
    with pytest.raises(re.error):
        f = field.parseString('___/[0-9')

    # combined with a length validator
    f = field.parseString('___[10]/[a-zA-Z]+')
    assert f.type == 'text'
    assert f.length == 10
    assert f.asDict() == {
        'length': 10,
        'type': 'text',
        'regex': re.compile('[a-zA-Z]+')
    }


def test_textarea() -> None:

    field = textarea()

    f = field.parseString("...")
    assert f.type == 'textarea'
    assert not f.rows
    assert f.asDict() == {'type': 'textarea'}

    f = field.parseString("...[15]")
    assert f.type == 'textarea'
    assert f.rows == 15
    assert f.asDict() == {'rows': 15, 'type': 'textarea'}


def test_password() -> None:

    field = password()

    f = field.parseString("***")
    assert f.type == 'password'
    assert f.asDict() == {'type': 'password'}


def test_email() -> None:

    field = email()

    f = field.parseString("@@@")
    assert f.type == 'email'
    assert f.asDict() == {'type': 'email'}


def test_url() -> None:

    field = url()

    f = field.parseString("http://")
    assert f.type == 'url'
    assert f.asDict() == {'type': 'url'}

    f = field.parseString("https://")
    assert f.type == 'url'
    assert f.asDict() == {'type': 'url'}


def test_video_url() -> None:

    field = video_url()

    f = field.parseString("video-url")
    assert f.type == 'video_url'
    assert f.asDict() == {'type': 'video_url'}


def test_valid_date_range() -> None:
    dr = valid_date_range().parseString('(..today)')
    assert dr.valid_date_range.start is None
    assert dr.valid_date_range.stop == relativedelta()

    dr = valid_date_range().parseString('(-4 years..+2 months)')
    assert dr.valid_date_range.start == relativedelta(years=-4)
    assert dr.valid_date_range.stop == relativedelta(months=+2)

    dr = valid_date_range().parseString('(-22 weeks..+180 days)')
    assert dr.valid_date_range.start == relativedelta(weeks=-22)
    assert dr.valid_date_range.stop == relativedelta(days=+180)

    dr = valid_date_range().parseString('(2010.01.01..2020.01.01)')
    assert dr.valid_date_range.start == dateobj(2010, 1, 1)
    assert dr.valid_date_range.stop == dateobj(2020, 1, 1)


def test_valid_date_range_invalid_date() -> None:
    with pytest.raises(ParseFatalException):
        valid_date_range().parseString('(..2000.20.45)')


def test_valid_date_range_invalid_mixed_range() -> None:
    with pytest.raises(ParseFatalException):
        valid_date_range().parseString('(2010.01.01..today)')


def test_valid_date_range_invalid_range_order() -> None:
    with pytest.raises(ParseFatalException):
        valid_date_range().parseString('(today..today)')

    with pytest.raises(ParseFatalException):
        valid_date_range().parseString('(-350 days..-1 years)')

    with pytest.raises(ParseFatalException):
        valid_date_range().parseString('(2020.01.01..2010.01.01)')


def test_dates() -> None:
    field = date().parseString('YYYY.MM.DD')
    assert field.asDict() == {'type': 'date'}

    field = datetime().parseString('YYYY.MM.DD HH:MM')
    assert field.asDict() == {'type': 'datetime'}

    field = time().parseString('HH:MM')
    assert field.asDict() == {'type': 'time'}


def test_dates_with_valid_date_range() -> None:
    field = date().parseString('YYYY.MM.DD (today..)')
    assert field.asDict() == {
        'type': 'date',
        'valid_date_range': {'start': relativedelta(), 'stop': None}
    }

    field = datetime().parseString('YYYY.MM.DD HH:MM (..today)')
    assert field.asDict() == {
        'type': 'datetime',
        'valid_date_range': {'start': None, 'stop': relativedelta()}
    }


def test_dates_with_invalid_date_range() -> None:
    with pytest.raises(ParseFatalException):
        date().parseString('YYYY.MM.DD (-350 days..-1 years)')

    with pytest.raises(ParseFatalException):
        datetime().parseString('YYYY.MM.DD HH:MM (today..today)')


def test_stdnum() -> None:
    field = stdnum()

    f = field.parseString("#test")
    assert f.type == 'stdnum'
    assert f.format == 'test'
    assert f.asDict() == {'type': 'stdnum', 'format': 'test'}

    f = field.parseString("# test")
    assert f.type == 'stdnum'
    assert f.format == 'test'
    assert f.asDict() == {'type': 'stdnum', 'format': 'test'}

    f = field.parseString("# asdf.asdf")
    assert f.type == 'stdnum'
    assert f.format == 'asdf.asdf'
    assert f.asDict() == {'type': 'stdnum', 'format': 'asdf.asdf'}


def test_radio() -> None:

    field = radio()

    f = field.parseString("( ) Male")
    assert f.type == 'radio'
    assert f.label == 'Male'
    assert not f.checked

    f = field.parseString("(x) Space Alien")
    assert f.type == 'radio'
    assert f.label == 'Space Alien'
    assert f.checked


def test_checkbox() -> None:

    field = checkbox()

    f = field.parseString("[x] German")
    assert f.type == 'checkbox'
    assert f.label == 'German'
    assert f.checked

    f = field.parseString("[ ] Swiss German")
    assert f.type == 'checkbox'
    assert f.label == 'Swiss German'
    assert not f.checked

    # non-latin1 character in label (en dash)
    # FIXME: Long-term we want this to be an error, but not for
    #        existing form code
    f = field.parseString("[ ] Read–only")
    assert f.type == 'checkbox'
    assert f.label == 'Read'
    assert not f.checked


def test_fileinput() -> None:

    field = fileinput()

    f = field.parseString("*.*")
    assert f.type == 'fileinput'
    assert f.extensions == ['*']

    f = field.parseString("*.pdf")
    assert f.type == 'fileinput'
    assert f.extensions == ['pdf']

    f = field.parseString("*.bat")
    assert f.type == 'fileinput'
    assert f.extensions == ['bat']

    f = field.parseString("*.png|*.jpg|*.gif")
    assert f.type == 'fileinput'
    assert f.extensions == ['png', 'jpg', 'gif']

    f = field.parseString("*.pdf (multiple)")
    assert f.type == 'multiplefileinput'
    assert f.extensions == ['pdf']


def test_prices() -> None:
    field = radio()

    f = field.parseString("( ) Default Choice (100 CHF)")
    assert f.type == 'radio'
    assert f.label == 'Default Choice'
    assert not f.checked
    assert f.pricing.amount == Decimal('100.00')
    assert f.pricing.currency == 'CHF'
    assert not f.pricing.credit_card_payment
    assert not f.dicount

    f = field.parseString("(x) Luxurious Choice (200 CHF)")
    assert f.type == 'radio'
    assert f.label == 'Luxurious Choice'
    assert f.checked
    assert f.pricing.amount == Decimal('200.00')
    assert f.pricing.currency == 'CHF'
    assert not f.pricing.credit_card_payment
    assert not f.dicount

    f = field.parseString("(x) Mail delivery (5 CHF!)")
    assert f.type == 'radio'
    assert f.label == 'Mail delivery'
    assert f.checked
    assert f.pricing.amount == Decimal('5.00')
    assert f.pricing.currency == 'CHF'
    assert f.pricing.credit_card_payment
    assert not f.dicount

    f = field.parseString("(x) Mail delivery (Local) (5 CHF!)")
    assert f.type == 'radio'
    assert f.label == 'Mail delivery (Local)'
    assert f.checked
    assert f.pricing.amount == Decimal('5.00')
    assert f.pricing.currency == 'CHF'
    assert f.pricing.credit_card_payment
    assert not f.dicount

    field = checkbox()

    f = field.parseString("[x] Extra Luggage (150.50 USD)")
    assert f.type == 'checkbox'
    assert f.label == 'Extra Luggage'
    assert f.checked
    assert f.pricing.amount == Decimal('150.50')
    assert f.pricing.currency == 'USD'
    assert not f.pricing.credit_card_payment
    assert not f.dicount

    f = field.parseString("[ ] Priority Boarding (15.00 USD)")
    assert f.type == 'checkbox'
    assert f.label == 'Priority Boarding'
    assert not f.checked
    assert f.pricing.amount == Decimal('15.00')
    assert f.pricing.currency == 'USD'
    assert not f.pricing.credit_card_payment
    assert not f.dicount

    f = field.parseString("[ ] Discount (-5.00 USD)")
    assert f.type == 'checkbox'
    assert f.label == 'Discount'
    assert not f.checked
    assert f.pricing.amount == Decimal('-5.00')
    assert f.pricing.currency == 'USD'
    assert not f.pricing.credit_card_payment
    assert not f.dicount

    f = field.parseString("[ ] Discount (For Kids) (-5.00 USD)")
    assert f.type == 'checkbox'
    assert f.label == 'Discount (For Kids)'
    assert not f.checked
    assert f.pricing.amount == Decimal('-5.00')
    assert f.pricing.currency == 'USD'
    assert not f.pricing.credit_card_payment
    assert not f.dicount

    f = field.parseString("[x] Mail delivery (5 CHF!)")
    assert f.type == 'checkbox'
    assert f.label == 'Mail delivery'
    assert f.checked
    assert f.pricing.amount == Decimal('5.00')
    assert f.pricing.currency == 'CHF'
    assert f.pricing.credit_card_payment
    assert not f.dicount

    field = integer_range_field()
    f = field.parseString("0..30 (1.00 CHF)")
    assert f.type == 'integer_range'
    assert f[0] == range(0, 30)
    assert f.pricing.amount == Decimal('1.00')
    assert f.pricing.currency == 'CHF'
    assert not f.pricing.credit_card_payment

    f = field.parseString("5..10 (2 USD!)")
    assert f.type == 'integer_range'
    assert f[0] == range(5, 10)
    assert f.pricing.amount == Decimal('2')
    assert f.pricing.currency == 'USD'
    assert f.pricing.credit_card_payment

    f = field.parseString("0..10")
    assert f.type == 'integer_range'
    assert f[0] == range(0, 10)
    assert not f.pricing


def test_discount() -> None:
    field = radio()

    f = field.parseString("( ) Default Choice (25%)")
    assert f.type == 'radio'
    assert f.label == 'Default Choice'
    assert not f.checked
    assert f.discount.amount == Decimal('25')
    assert not f.pricing

    f = field.parseString("(x) Luxurious Choice (-100 %)")
    assert f.type == 'radio'
    assert f.label == 'Luxurious Choice'
    assert f.checked
    assert f.discount.amount == Decimal('-100')
    assert not f.pricing

    f = field.parseString("(x) Mail delivery (33.3 %)")
    assert f.type == 'radio'
    assert f.label == 'Mail delivery'
    assert f.checked
    assert f.discount.amount == Decimal('33.3')
    assert not f.pricing

    f = field.parseString("(x) Mail delivery (Local) (33.3 %)")
    assert f.type == 'radio'
    assert f.label == 'Mail delivery (Local)'
    assert f.checked
    assert f.discount.amount == Decimal('33.3')
    assert not f.pricing

    f = field.parseString("(x) Mail delivery (33.3%) (Local)")
    assert f.type == 'radio'
    assert f.label == 'Mail delivery'
    assert f.checked
    assert f.discount.amount == Decimal('33.3')
    assert not f.pricing

    # relaxed end line requirement
    f = field.parseString("(x) Mail delivery (33.3%)   ")
    assert f.type == 'radio'
    assert f.label == 'Mail delivery'
    assert f.checked
    assert f.discount.amount == Decimal('33.3')
    assert not f.pricing

    field = checkbox()

    f = field.parseString("[x] Extra Luggage (99.15%)")
    assert f.type == 'checkbox'
    assert f.label == 'Extra Luggage'
    assert f.checked
    assert f.discount.amount == Decimal('99.15')
    assert not f.pricing

    f = field.parseString("[ ] Priority Boarding (0 %)")
    assert f.type == 'checkbox'
    assert f.label == 'Priority Boarding'
    assert not f.checked
    assert f.discount.amount == Decimal('0')
    assert not f.pricing

    f = field.parseString("[ ] Discount (50%)")
    assert f.type == 'checkbox'
    assert f.label == 'Discount'
    assert not f.checked
    assert f.discount.amount == Decimal('50')
    assert not f.pricing

    f = field.parseString("[ ] Discount (For Kids) (50%)")
    assert f.type == 'checkbox'
    assert f.label == 'Discount (For Kids)'
    assert not f.checked
    assert f.discount.amount == Decimal('50')
    assert not f.pricing

    f = field.parseString("[ ] Discount (50%) (For Kids)")
    assert f.type == 'checkbox'
    assert f.label == 'Discount'
    assert not f.checked
    assert f.discount.amount == Decimal('50')
    assert not f.pricing

    # relaxed end line requirement
    f = field.parseString("[ ] Discount (50%)    ")
    assert f.type == 'checkbox'
    assert f.label == 'Discount'
    assert not f.checked
    assert f.discount.amount == Decimal('50')
    assert not f.pricing


def test_non_prices() -> None:
    field = radio()

    f = field.parseString("( ) Foobar (Some Information)")
    assert f.label == 'Foobar (Some Information)'

    f = field.parseString("( ) Foobar (1up)")
    assert f.label == 'Foobar (1up)'

    f = field.parseString("( ) Foobar (123.23 USD)")
    assert f.label == 'Foobar'


def test_decimal() -> None:
    field = decimal()

    assert field.parseString('123.45')[0] == Decimal('123.45')
    assert field.parseString('123')[0] == Decimal('123')
    assert field.parseString('0.5')[0] == Decimal('0.5')
    assert field.parseString('-10.0')[0] == Decimal('-10.0')


def test_currency() -> None:
    field = currency()

    assert field.parseString('CHF')[0] == 'CHF'
    assert field.parseString('usd')[0] == 'USD'
    assert field.parseString('Cny')[0] == 'CNY'


def test_integer_range() -> None:
    field = integer_range_field()

    assert field.parseString('0..10')[0] == range(0, 10)
    assert field.parseString('-10..100')[0] == range(-10, 100)
    assert field.parseString('0..-20')[0] == range(0, -20)
    assert field.parseString('-10..-20')[0] == range(-10, -20)


def test_decimal_range() -> None:
    field = decimal_range_field()

    assert field.parseString(
        '0.00..10.00')[0] == decimal_range('0.0', '10.0')
    assert field.parseString(
        '-10.00..100.00')[0] == decimal_range('-10.0', '100.0')
    assert field.parseString(
        '0.00..-20.00')[0] == decimal_range('0.0', '-20.0')
    assert field.parseString(
        '-10.00..-20.00')[0] == decimal_range('-10.0', '-20.0')


def test_code() -> None:
    field = code()

    assert field.parseString('<markdown>').syntax == 'markdown'
    assert field.parseString('<markdown>').type == 'code'


def test_chip_nr() -> None:
    field = chip_nr()

    f = field.parseString("chip-nr")
    assert f.type == 'chip_nr'
    assert f.asDict() == {'type': 'chip_nr'}
