from decimal import Decimal
from onegov.form.parser.grammar import (
    checkbox,
    date,
    datetime,
    decimal,
    currency,
    email,
    field_identifier,
    fileinput,
    password,
    radio,
    stdnum,
    text_without,
    textarea,
    textfield,
    time,
    with_whitespace_inside
)


def test_text_without():
    assert text_without('?!').parseString('what')[0] == 'what'
    assert text_without('?!').parseString('what what?')[0] == 'what'
    assert text_without('?!').parseString('what!')[0] == 'what'
    assert text_without('?').parseString('what!')[0] == 'what!'


def test_with_whitespace_inside():
    text = text_without('')
    assert with_whitespace_inside(text).parseString("a b")[0] == "a b"
    assert with_whitespace_inside(text).parseString("a b ")[0] == "a b"
    assert with_whitespace_inside(text).parseString("a  b ")[0] == "a"


def test_field_identifier():
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


def test_textfield():

    field = textfield()

    f = field.parseString('___')
    assert f.type == 'text'
    assert not f.length
    f.asDict() == {'length': None, 'type': 'text'}

    f = field.parseString('___[25]')
    assert f.type == 'text'
    assert f.length == 25
    f.asDict() == {'length': 25, 'type': 'text'}


def test_textarea():

    field = textarea()

    f = field.parseString("...")
    assert f.type == 'textarea'
    assert not f.rows
    f.asDict() == {'type': 'textarea'}

    f = field.parseString("...[15]")
    assert f.type == 'textarea'
    assert f.rows == 15
    f.asDict() == {'rows': 15, 'type': 'textarea'}


def test_password():

    field = password()

    f = field.parseString("***")
    assert f.type == 'password'
    assert f.asDict() == {'type': 'password'}


def test_email():

    field = email()

    f = field.parseString("@@@")
    assert f.type == 'email'
    assert f.asDict() == {'type': 'email'}


def test_dates():

    field = date().searchString('YYYY.MM.DD')
    field.asDict() == {'type': 'date', 'label': 'Date'}

    field = datetime().searchString('YYYY.MM.DD HH:MM')
    field.asDict() == {'type': 'datetime', 'label': 'Datetime'}

    field = time().searchString('HH:MM')
    field.asDict() == {'type': 'time', 'label': 'Time'}


def test_stdnum():
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


def test_radio():

    field = radio()

    f = field.parseString("( ) Male")
    assert f.type == 'radio'
    assert f.label == 'Male'
    assert not f.checked

    f = field.parseString("(x) Space Alien")
    assert f.type == 'radio'
    assert f.label == 'Space Alien'
    assert f.checked


def test_checkbox():

    field = checkbox()

    f = field.parseString("[x] German")
    assert f.type == 'checkbox'
    assert f.label == 'German'
    assert f.checked

    f = field.parseString("[ ] Swiss German")
    assert f.type == 'checkbox'
    assert f.label == 'Swiss German'
    assert not f.checked


def test_fileinput():

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


def test_prices():
    field = radio()

    f = field.parseString("( ) Default Choice (100 CHF)")
    assert f.type == 'radio'
    assert f.label == 'Default Choice'
    assert not f.checked
    assert f.pricing.amount == Decimal('100.00')
    assert f.pricing.currency == 'CHF'

    f = field.parseString("(x) Luxurious Choice (200 CHF)")
    assert f.type == 'radio'
    assert f.label == 'Luxurious Choice'
    assert f.checked
    assert f.pricing.amount == Decimal('200.00')
    assert f.pricing.currency == 'CHF'

    field = checkbox()

    f = field.parseString("[x] Extra Luggage (150.50 USD)")
    assert f.type == 'checkbox'
    assert f.label == 'Extra Luggage'
    assert f.checked
    assert f.pricing.amount == Decimal('150.50')
    assert f.pricing.currency == 'USD'

    f = field.parseString("[ ] Priority Boarding (15.00 USD)")
    assert f.type == 'checkbox'
    assert f.label == 'Priority Boarding'
    assert not f.checked
    assert f.pricing.amount == Decimal('15.00')
    assert f.pricing.currency == 'USD'

    f = field.parseString("[ ] Discount (-5.00 USD)")
    assert f.type == 'checkbox'
    assert f.label == 'Discount'
    assert not f.checked
    assert f.pricing.amount == Decimal('-5.00')
    assert f.pricing.currency == 'USD'


def test_decimal():
    field = decimal()

    assert field.parseString('123.45')[0] == Decimal('123.45')
    assert field.parseString('123')[0] == Decimal('123')
    assert field.parseString('0.5')[0] == Decimal('0.5')
    assert field.parseString('-10.0')[0] == Decimal('-10.0')


def test_currency():
    field = currency()

    assert field.parseString('CHF')[0] == 'CHF'
    assert field.parseString('usd')[0] == 'USD'
    assert field.parseString('Cny')[0] == 'CNY'
