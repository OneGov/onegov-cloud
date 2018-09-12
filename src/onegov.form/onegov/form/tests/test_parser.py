import pytest

from decimal import Decimal
from onegov.form import Form, errors, find_field
from onegov.form import parse_formcode, parse_form, flatten_fieldsets
from onegov.pay import Price
from textwrap import dedent
from webob.multidict import MultiDict
from wtforms import FileField
from wtforms import validators
from wtforms.fields.html5 import (
    DateField,
    DateTimeLocalField,
    EmailField,
    URLField,
)
from wtforms_components import TimeField


def test_parse_text():
    text = dedent("""
        First name * = ___
        Last name = ___
        Country = ___[50]
        Comment = ...[8]
        Zipcode = ___[4]/[0-9]*
        Currency = ___/[A-Z]{3}
    """)

    form_class = parse_form(text)
    form = form_class()

    fields = form._fields.values()
    assert len(fields) == 6

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

    assert form.zipcode.label.text == 'Zipcode'
    assert len(form.zipcode.validators) == 3
    assert isinstance(form.zipcode.validators[0], validators.Optional)
    assert isinstance(form.zipcode.validators[1], validators.Length)
    assert isinstance(form.zipcode.validators[2], validators.Regexp)

    assert form.currency.label.text == 'Currency'
    assert len(form.currency.validators) == 2
    assert isinstance(form.currency.validators[0], validators.Optional)
    assert isinstance(form.currency.validators[1], validators.Regexp)


def test_regex_validation():
    form_class = parse_form("Zipcode = ___[4]/[0-9]+")

    form = form_class(MultiDict([('zipcode', 'abcd')]))
    form.validate()
    assert form.errors

    form = form_class(MultiDict([('zipcode', '12345')]))
    form.validate()
    assert form.errors

    form = form_class(MultiDict([('zipcode', '1234')]))
    form.validate()
    assert not form.errors

    form_class = parse_form("Zipcode = ___/^(yes|no)$")

    form = form_class(MultiDict([('zipcode', 'yess')]))
    form.validate()
    assert form.errors

    form = form_class(MultiDict([('zipcode', 'noes')]))
    form.validate()
    assert form.errors

    form = form_class(MultiDict([('zipcode', 'yes')]))
    form.validate()
    assert not form.errors

    form = form_class(MultiDict([('zipcode', 'no')]))
    form.validate()
    assert not form.errors


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


def test_parse_syntax():
    form = parse_form("Text = <markdown>")()
    assert len(form._fields.values()) == 1
    assert form.text.label.text == 'Text'
    assert form.text.render_kw == {'data-editor': 'markdown'}


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


def test_parse_url():
    form = parse_form("Url = http://")()

    assert form.url.label.text == 'Url'
    assert isinstance(form.url, URLField)


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


def test_parse_radio_escape():

    text = dedent("""
        # "For sure"
        Let's go =
            ( ) Yeah, let's
            (x) No, let's not
    """)

    form = parse_form(text)()

    assert len(form._fields) == 1
    assert form.for_sure_let_s_go.choices == [
        ("Yeah, let's", "Yeah, let's"),
        ("No, let's not", "No, let's not"),
    ]
    assert form.for_sure_let_s_go.default == "No, let's not"


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


def test_parse_radio_with_pricing():

    text = dedent("""
        Drink =
            ( ) Coffee (2.50 CHF)
            (x) Tea (1.50 CHF)
    """)

    form = parse_form(text)()
    assert form.drink.pricing.rules == {
        'Coffee': Price(Decimal(2.5), 'CHF'),
        'Tea': Price(Decimal(1.5), 'CHF')
    }


def test_parse_checkbox_with_pricing():

    text = dedent("""
        Extras =
            [ ] Bacon (2.50 CHF)
            [x] Cheese (1.50 CHF)
    """)

    form = parse_form(text)()
    assert form.extras.pricing.rules == {
        'Bacon': Price(Decimal(2.5), 'CHF'),
        'Cheese': Price(Decimal(1.5), 'CHF')
    }
    assert form.extras.pricing.rules['Bacon'].amount == Decimal(2.5)
    assert form.extras.pricing.rules['Bacon'].currency == 'CHF'


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


def test_parse_formcode():
    fieldsets = parse_formcode("""
        # General
        First Name *= ___
        Last Name = ___[10]

        # Order
        Products =
            [ ] Pizza
                Type =
                    (x) Default
                    ( ) Gluten-Free
            [x] Burger
    """)

    assert len(fieldsets) == 2
    assert fieldsets[0].label == 'General'

    assert fieldsets[0].fields[0].type == 'text'
    assert fieldsets[0].fields[0].required
    assert fieldsets[0].fields[0].maxlength is None
    assert fieldsets[0].fields[0].id == 'general_first_name'

    assert fieldsets[0].fields[1].type == 'text'
    assert not fieldsets[0].fields[1].required
    assert fieldsets[0].fields[1].maxlength == 10
    assert fieldsets[0].fields[1].id == 'general_last_name'

    assert fieldsets[1].label == 'Order'
    assert fieldsets[1].fields[0].type == 'checkbox'

    assert fieldsets[1].fields[0].label == 'Products'
    assert fieldsets[1].fields[0].id == 'order_products'

    assert fieldsets[1].fields[0].choices[0].key == 'Pizza'
    assert fieldsets[1].fields[0].choices[0].label == 'Pizza'
    assert not fieldsets[1].fields[0].choices[0].selected

    assert fieldsets[1].fields[0].choices[1].key == 'Burger'
    assert fieldsets[1].fields[0].choices[1].label == 'Burger'
    assert fieldsets[1].fields[0].choices[1].selected

    assert fieldsets[1].fields[0].choices[0].fields[0].label == 'Type'
    assert fieldsets[1].fields[0].choices[0].fields[0].id \
        == 'order_products_type'
    assert fieldsets[1].fields[0].choices[0].fields[0].choices[0].selected
    assert not fieldsets[1].fields[0].choices[0].fields[0].choices[1].selected
    assert fieldsets[1].fields[0].choices[0].fields[0].choices[0].label \
        == 'Default'
    assert fieldsets[1].fields[0].choices[0].fields[0].choices[1].label \
        == 'Gluten-Free'


def test_parse_formcode_duplicate_fieldname():
    with pytest.raises(errors.DuplicateLabelError):
        parse_formcode("""
            # General
            Foo *= ___
            Foo = ___[10]
        """)

    with pytest.raises(errors.DuplicateLabelError):
        parse_formcode("""
            Foo *= ___
            Foo = ___[10]
        """)

    with pytest.raises(errors.DuplicateLabelError):
        parse_formcode("""
            # General
            Sure *=
                ( ) Yes
                ( ) No
                    Foo = ___
                    Foo = ___
        """)

    with pytest.raises(errors.DuplicateLabelError):
        parse_formcode("""
            Sure *=
                ( ) Yes
                ( ) No
                    Foo = ___
                    Foo = ___
        """)


def test_flatten_fieldsets():
    fieldsets = parse_formcode("""
        # General
        First Name *= ___
        Last Name *= ___[10]

        # Order
        Products =
            [ ] Pizza
                Type =
                    (x) Default
                    ( ) Gluten-Free
            [x] Burger
    """)

    fields = list(flatten_fieldsets(fieldsets))

    assert len(fields) == 4
    assert fields[0].label == 'First Name'
    assert fields[1].label == 'Last Name'
    assert fields[2].label == 'Products'
    assert fields[3].label == 'Type'


def test_integer_range():

    form_class = parse_form("Age = 21..150")
    form = form_class(MultiDict([
        ('age', '')
    ]))

    form.validate()
    assert not form.errors

    form_class = parse_form("Age *= 21..150")
    form = form_class(MultiDict([
        ('age', '')
    ]))

    form.validate()
    assert form.errors

    form_class = parse_form("Age *= 21..150")
    form = form_class(MultiDict([
        ('age', '20')
    ]))

    form.validate()
    assert form.errors

    form_class = parse_form("Age *= 21..150")
    form = form_class(MultiDict([
        ('age', '151')
    ]))

    form.validate()
    assert form.errors

    form_class = parse_form("Age *= 21..150")
    form = form_class(MultiDict([
        ('age', '21')
    ]))

    form.validate()
    assert not form.errors


def test_decimal_range():

    form_class = parse_form("Percentage = 0.00..100.00")
    form = form_class(MultiDict([
        ('percentage', '')
    ]))

    form.validate()
    assert not form.errors

    form_class = parse_form("Percentage *= 0.00..100.00")
    form = form_class(MultiDict([
        ('percentage', '')
    ]))

    form.validate()
    assert form.errors

    form_class = parse_form("Percentage = 0.00..100.00")
    form = form_class(MultiDict([
        ('percentage', '-1')
    ]))

    form.validate()
    assert form.errors

    form_class = parse_form("Percentage = 0.00..100.00")
    form = form_class(MultiDict([
        ('percentage', '101')
    ]))

    form.validate()
    assert form.errors

    form_class = parse_form("Percentage = 0.00..100.00")
    form = form_class(MultiDict([
        ('percentage', '33.33')
    ]))

    form.validate()
    assert not form.errors


def test_field_ids():
    fs = parse_formcode("""
        First Name *= ___
        Last Name = ___[10]

        # My Order
        Products =
            [ ] Pizza
                Type =
                    (x) Default
                    ( ) Gluten-Free
            [x] Burger
    """)

    assert fs[0].fields[0].id == 'first_name'
    assert fs[0].fields[0].human_id == 'First Name'
    assert fs[0].fields[1].id == 'last_name'
    assert fs[0].fields[1].human_id == 'Last Name'
    assert fs[1].fields[0].id == 'my_order_products'
    assert fs[1].fields[0].human_id == 'My Order/Products'
    assert fs[1].fields[0].choices[0].fields[0].id == 'my_order_products_type'
    assert fs[1].fields[0].choices[0].fields[0].human_id\
        == 'My Order/Products/Type'

    assert find_field(fs, None) is fs[0]
    assert find_field(fs, 'my_order') is fs[1]
    assert find_field(fs, 'My Order') is fs[1]
    assert find_field(fs, 'first_name').id == 'first_name'
    assert find_field(fs, 'First Name').id == 'first_name'
    assert find_field(fs, 'last_name').id == 'last_name'
    assert find_field(fs, 'Last Name').id == 'last_name'
    assert find_field(fs, 'my_order_products').id == 'my_order_products'
    assert find_field(fs, 'My Order/Products').id == 'my_order_products'
    assert find_field(fs, 'my_order_products_type').id\
        == 'my_order_products_type'
    assert find_field(fs, 'My Order/Products/Type').id\
        == 'my_order_products_type'

    assert fs[0].find_field('first_name').id == 'first_name'
    assert fs[0].find_field('First Name').id == 'first_name'
    assert fs[1].find_field('first_name') is None
    assert fs[1].find_field('First Name') is None


@pytest.mark.parametrize("field,invalid", [
    ('@@@', 'foo'),
    ('0..99', 100),
    ('0.00..99.99', 100.00),
    ('# iban', 'foo')
])
def test_dependency_validation_chain(field, invalid):
    for required in (True, False):
        code = """
            select *=
                ( ) ya
                    value {}= {}
                (x) no
        """.format(required and '*' or '', field)

        form = parse_form(code)

        # we cannot supply an empty value if the depencency is fulfilled
        # and an input is required
        if required:
            assert not form(data={'select': 'ya'}).validate()

        # we can supply an empty value if the dependency is not fulfilled
        assert form(data={'select': 'no'}).validate()

        # we cannot supply an invalid value in any case
        inv = invalid
        assert not form(data={'select': 'no', 'select_value': inv}).validate()
        assert not form(data={'select': 'ya', 'select_value': inv}).validate()
