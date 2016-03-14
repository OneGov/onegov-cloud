import pytest

from onegov.form import Form, errors
from onegov.form.parser import parse_form
from textwrap import dedent
from webob.multidict import MultiDict
from wtforms import FileField
from wtforms import validators
from wtforms.fields.html5 import (
    DateField,
    DateTimeLocalField,
    EmailField
)
from wtforms_components import TimeField


def test_parse_text():
    text = dedent("""
        First name * = ___
        Last name = ___
        Country = ___[50]
        Comment = ...[8]
    """)

    form_class = parse_form(text)
    form = form_class()

    fields = form._fields.values()
    assert len(fields) == 4

    assert form.first_name.label.text == 'First name'
    assert len(form.first_name.validators) == 1
    assert isinstance(form.first_name.validators[0], validators.DataRequired)

    assert form.last_name.label.text == 'Last name'
    assert len(form.last_name.validators) == 1
    assert isinstance(form.country.validators[0], validators.Optional)

    assert form.country.label.text == 'Country'
    assert len(form.country.validators) == 2
    assert isinstance(form.country.validators[0], validators.Optional)
    assert isinstance(form.country.validators[1], validators.Length)

    assert form.comment.label.text == 'Comment'
    assert form.comment.widget(form.comment) == (
        '<textarea id="comment" name="comment" rows="8"></textarea>')


def test_parse_different_base_class():

    class Test(Form):
        foo = 'bar'

    form_class = parse_form('x = ___', Test)
    assert form_class.foo == 'bar'
    assert isinstance(form_class(), Test)


def test_unicode():
    text = dedent("""
        # Persönliche Informationen
        Bürgerort = ___
        Geschlecht =
            ( ) Männlich
            ( ) Weiblich
    """)

    form = parse_form(text)()

    assert form.personliche_informationen_burgerort.label.text == 'Bürgerort'
    assert 'Persönliche Informationen' == form.fieldsets[0].label
    assert form.personliche_informationen_geschlecht.choices == [
        ('Männlich', 'Männlich'),
        ('Weiblich', 'Weiblich')
    ]


def test_parse_fieldsets():
    text = dedent("""
        # Name
        First name = ___
        Last name = ___

        # Address
        Street = ___

        # ...
        Comment = ___
    """)

    form_class = parse_form(text)
    form = form_class()

    fields = form._fields.values()
    assert len(fields) == 4

    fieldsets = form.fieldsets
    assert len(fieldsets) == 3

    assert len(fieldsets[0]) == 2
    assert fieldsets[0].label == 'Name'
    assert fieldsets[0].is_visible
    assert fieldsets[0]['name_first_name'].label.text == 'First name'
    assert fieldsets[0]['name_last_name'].label.text == 'Last name'

    assert len(fieldsets[1]) == 1
    assert fieldsets[1].label == 'Address'
    assert fieldsets[1].is_visible
    assert fieldsets[1]['address_street'].label.text == 'Street'

    assert len(fieldsets[2]) == 1
    assert fieldsets[2].label is None
    assert not fieldsets[2].is_visible
    assert fieldsets[2]['comment'].label.text == 'Comment'


def test_fieldset_field_ids():
    text = dedent("""
        First Name = ___

        # Spouse
        First Name = ___
    """)

    form = parse_form(text)()
    hasattr(form, 'first_name')
    hasattr(form, 'spouse_first_name')


def test_duplicate_field():
    text = dedent("""
        First Name = ___
        First Name = ___
    """)

    with pytest.raises(errors.DuplicateLabelError):
        parse_form(text)


def test_dependent_field():
    text = dedent("""
        Comment =
            [ ] I have one
                Comment = ...

        # Extra
        Comment =
            [ ] I have one
                Comment = ...
    """)

    form = parse_form(text)
    assert hasattr(form, 'comment')
    assert hasattr(form, 'comment_comment')
    assert hasattr(form, 'extra_comment')
    assert hasattr(form, 'extra_comment_comment')


def test_parse_email():
    form = parse_form("E-Mail = @@@")()

    assert form.e_mail.label.text == 'E-Mail'
    assert isinstance(form.e_mail, EmailField)


def test_parse_date():
    form = parse_form("Date = YYYY.MM.DD")()

    assert form.date.label.text == 'Date'
    assert isinstance(form.date, DateField)


def test_parse_datetime():
    form = parse_form("Datetime = YYYY.MM.DD HH:MM")()

    assert form.datetime.label.text == 'Datetime'
    assert isinstance(form.datetime, DateTimeLocalField)


def test_parse_time():
    form = parse_form("Time = HH:MM")()

    assert form.time.label.text == 'Time'
    assert isinstance(form.time, TimeField)


def test_parse_fileinput():
    form = parse_form("File = *.pdf|*.doc")()

    assert form.file.label.text == 'File'
    assert isinstance(form.file, FileField)


def test_parse_radio():

    text = dedent("""
        Gender =
            ( ) Male
            (x) Female
    """)

    form = parse_form(text)()

    assert len(form._fields) == 1
    assert form.gender.choices == [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    assert form.gender.default == 'Female'


def test_parse_checkbox():

    text = dedent("""
        Extras =
            [ ] Extra Luggage
            [x] Priority Seating
            [x] Early Boarding
    """)

    form = parse_form(text)()

    assert len(form._fields) == 1
    assert form.extras.choices == [
        ('Extra Luggage', 'Extra Luggage'),
        ('Priority Seating', 'Priority Seating'),
        ('Early Boarding', 'Early Boarding'),
    ]
    assert form.extras.default == ['Priority Seating', 'Early Boarding']


def test_dependent_validation():

    text = dedent("""
        Payment * =
            ( ) Bill
                Address * = ___
            ( ) Credit Card
                Credit Card Number * = ___
    """)

    form_class = parse_form(text)
    assert len(form_class()._fields) == 3

    form = form_class(MultiDict([
        ('payment', 'Bill'),
        ('payment_address', 'Destiny Lane')
    ]))

    form.validate()
    assert not form.errors

    form = form_class(MultiDict([
        ('payment', 'Bill'),
    ]))

    form.validate()
    assert form.errors == {'payment_address': ['This field is required.']}

    form = form_class(MultiDict([
        ('payment', 'Credit Card'),
    ]))

    form.validate()
    assert form.errors == {
        'payment_credit_card_number': ['This field is required.']}

    form = form_class(MultiDict([
        ('payment', 'Credit Card'),
        ('payment_credit_card_number', '123')
    ]))

    form.validate()
    assert not form.errors

    assert 'data-depends-on="payment/Bill"' in (
        form.payment_address.widget(form.payment_address))
    assert 'data-depends-on="payment/Credit Card"' in (
        form.payment_credit_card_number.widget(
            form.payment_credit_card_number))


def test_nested_regression():

    text = dedent("""
        Delivery * =
            (x) I want it delivered
                Alternate Address =
                    (x) No
                    ( ) Yes
                        Street = ___
                        Town = ___
            ( ) I want to pick it up
        Kommentar = ...
    """)

    form_class = parse_form(text)

    form = form_class()

    assert len(form._fields) == 5
    assert len(form.delivery.choices) == 2
    assert len(form.delivery_alternate_address.choices) == 2

    assert hasattr(form, 'delivery_alternate_address_street')
    assert hasattr(form, 'delivery_alternate_address_town')


def test_stdnum_field():

    form_class = parse_form("Bank Account = # iban")
    form = form_class(MultiDict([
        ('bank_account', '')
    ]))

    form.validate()
    assert not form.errors

    form = form_class(MultiDict([
        ('bank_account', 'CH93 0076 2011 6238 5295 7')
    ]))

    form.validate()
    assert not form.errors

    form = form_class(MultiDict([
        ('bank_account', 'CH93 0000 2011 6238 5295 7')
    ]))

    form.validate()
    assert form.errors

    with pytest.raises(ImportError):
        form_class = parse_form("Invalid = # asdf")

    form_class = parse_form("ahv = # ch.ssn")
    form = form_class(MultiDict([
        ('ahv', '756.9217.0769.85')
    ]))

    form.validate()
    assert not form.errors

    form = form_class(MultiDict([
        ('ahv', '756.9217.0769.12')
    ]))

    form.validate()
    assert form.errors


def test_optional_date():

    text = "Date = YYYY.MM.DD"

    form_class = parse_form(text)

    form = form_class(MultiDict([
        ('date', '30.02.2015')
    ]))

    form.validate()
    assert form.errors == {'date': ['Not a valid date value']}

    form = form_class(MultiDict([
        ('date', '')
    ]))

    form.validate()
    assert not form.errors


def test_invalid_syntax():
    with pytest.raises(errors.InvalidFormSyntax) as e:
        parse_form(".")
    assert e.value.line == 1

    with pytest.raises(errors.InvalidFormSyntax) as e:
        parse_form("Test = __")
    assert e.value.line == 1

    with pytest.raises(errors.InvalidFormSyntax) as e:
        parse_form('\n'.join((
            "# Fields",
            "",
            "First Name *= ___",
            "Last Name * __"
        )))
    assert e.value.line == 4

    with pytest.raises(errors.InvalidFormSyntax) as e:
        parse_form('\n'.join((
            "# Fields",
            "",
            "    [x] What",
        )))
    assert e.value.line == 3

    with pytest.raises(errors.InvalidFormSyntax) as e:
        parse_form('# Personalien')
    assert e.value.line == 1

    with pytest.raises(errors.InvalidFormSyntax) as e:
        parse_form('\n'.join((
            "Ort * = ___",
            "(x) 6. Klasse",
            "(x) 7. Klasse",
            "(x) 8. Klasse",
            "(x) 9. Klasse",
        )))
    assert e.value.line == 2
