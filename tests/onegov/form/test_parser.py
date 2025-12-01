from __future__ import annotations

import pytest

from dateutil.relativedelta import relativedelta
from decimal import Decimal
from onegov.form import Form, errors, find_field
from onegov.form import parse_formcode, parse_form, flatten_fieldsets
from onegov.form.errors import (
    InvalidIndentSyntax,
    InvalidCommentIndentSyntax,
    InvalidCommentLocationSyntax,
)
from onegov.form.fields import (
    DateTimeLocalField, MultiCheckboxField, TimeField, URLField, VideoURLField)
from onegov.form.parser.grammar import field_help_identifier
from onegov.form.validators import LaxDataRequired
from onegov.form.validators import ValidDateRange
from onegov.pay import Price
from textwrap import dedent
from webob.multidict import MultiDict
from wtforms.fields import DateField
from wtforms.fields import EmailField
from wtforms.fields import FileField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.validators import Length
from wtforms.validators import Optional
from wtforms.validators import Regexp


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from pyparsing import ParserElement, ParseResults


def parse(expr: ParserElement, text: str) -> ParseResults:
    return expr.parseString(text)


@pytest.mark.parametrize('comment,output', [
    ('<< Some text >>', 'Some text'),
    ('<< [Z](www.co.me) >>', '[Z](www.co.me)')
])
def test_help_field_identifier(comment: str, output: str) -> None:

    parsed_result = parse(field_help_identifier(), comment)
    assert parsed_result.message == output


def test_parse_text() -> None:
    text = dedent("""
        First name * = ___
        << Fill in all in UPPER case >>
        Last name = ___
        Country = ___[50]
        Comment = ...[8]
        Zipcode = ___[4]/[0-9]*
        Currency = ___/[A-Z]{3}
        << like EUR, CHF >>
    """)

    form_class = parse_form(text)
    form = form_class()

    fields = form._fields.values()
    assert len(fields) == 6

    assert isinstance(form['first_name'], StringField)
    assert form['first_name'].label.text == 'First name'
    assert form['first_name'].description == 'Fill in all in UPPER case'
    assert len(form['first_name'].validators) == 1
    assert isinstance(form['first_name'].validators[0], LaxDataRequired)

    assert isinstance(form['last_name'], StringField)
    assert form['last_name'].label.text == 'Last name'
    assert len(form['last_name'].validators) == 1
    assert isinstance(form['last_name'].validators[0], Optional)

    assert isinstance(form['country'], StringField)
    assert form['country'].label.text == 'Country'
    assert len(form['country'].validators) == 2
    assert isinstance(form['country'].validators[0], Optional)
    assert isinstance(form['country'].validators[1], Length)

    assert form['comment'].label.text == 'Comment'
    assert '<textarea id="comment" name="comment" rows="8">' in form[
        'comment'].widget(form['comment'], **form['comment'].render_kw)

    assert isinstance(form['zipcode'], StringField)
    assert form['zipcode'].label.text == 'Zipcode'
    assert len(form['zipcode'].validators) == 3
    assert isinstance(form['zipcode'].validators[0], Optional)
    assert isinstance(form['zipcode'].validators[1], Length)
    assert isinstance(form['zipcode'].validators[2], Regexp)

    assert isinstance(form['currency'], StringField)
    assert form['currency'].label.text == 'Currency'
    assert len(form['currency'].validators) == 2
    assert isinstance(form['currency'].validators[0], Optional)
    assert isinstance(form['currency'].validators[1], Regexp)
    assert form['currency'].description == 'like EUR, CHF'


def test_regex_validation() -> None:
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


def test_parse_different_base_class() -> None:

    class Test(Form):
        foo = 'bar'

    form_class = parse_form('x = ___', base_class=Test)
    assert form_class.foo == 'bar'
    assert isinstance(form_class(), Test)


def test_unicode() -> None:
    text = dedent("""
        # Persönliche Informationen
        Bürgerort = ___
        Geschlecht =
            ( ) Männlich
            ( ) Weiblich
    """)

    form = parse_form(text)()

    assert isinstance(form['personliche_informationen_geschlecht'], RadioField)
    assert form['personliche_informationen_burgerort'].label.text == (
        'Bürgerort')
    assert 'Persönliche Informationen' == form.fieldsets[0].label
    assert form['personliche_informationen_geschlecht'].choices == [
        ('Männlich', 'Männlich'),
        ('Weiblich', 'Weiblich')
    ]


def test_parse_fieldsets() -> None:
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


def test_parse_syntax() -> None:
    form = parse_form("Text = <markdown>\n<< # H1, ## H2 >>")()
    assert len(form._fields.values()) == 1
    assert form['text'].label.text == 'Text'
    assert form['text'].render_kw == {'data-editor': 'markdown'}
    assert form['text'].description == '# H1, ## H2'


def test_fieldset_field_ids() -> None:
    text = dedent("""
        First Name = ___

        # Spouse
        First Name = ___
        << No abbreviations, pls >>
    """)

    form = parse_form(text)()
    assert hasattr(form, 'first_name')
    assert hasattr(form, 'spouse_first_name')
    assert form.spouse_first_name.description == 'No abbreviations, pls'


def test_duplicate_field() -> None:
    text = dedent("""
        First Name = ___
        First Name = ___
    """)

    with pytest.raises(errors.DuplicateLabelError):
        parse_form(text)


def test_dependent_field() -> None:
    text = dedent("""
        Comment =
            [ ] I have one
                Comment = ...
        << first >>

        # Extra
        Comment =
            [ ] I have one
                Comment = ...
                << last >>
        << middle >>
    """)

    form = parse_form(text)
    assert hasattr(form, 'comment')
    assert form.comment.kwargs['description'] == 'first'
    assert hasattr(form, 'comment_comment')
    assert hasattr(form, 'extra_comment')
    assert form.extra_comment.kwargs['description'] == 'middle'
    assert hasattr(form, 'extra_comment_comment')
    assert form.extra_comment_comment.kwargs['description'] == 'last'


def test_parse_email() -> None:
    form = parse_form("E-Mail = @@@")()

    assert form['e_mail'].label.text == 'E-Mail'
    assert isinstance(form['e_mail'], EmailField)


def test_parse_url() -> None:
    form = parse_form("Url = http://")()

    assert form['url'].label.text == 'Url'
    assert isinstance(form['url'], URLField)


def test_parse_video_url() -> None:
    form = parse_form("Embedded Video = video-url")()

    assert form['embedded_video'].label.text == 'Embedded Video'
    assert isinstance(form['embedded_video'], VideoURLField)


def test_parse_date() -> None:
    form = parse_form("Date = YYYY.MM.DD")()

    assert form['date'].label.text == 'Date'
    assert isinstance(form['date'], DateField)
    assert not hasattr(form['date'].widget, 'min')
    assert not hasattr(form['date'].widget, 'max')
    assert len(form['date'].validators) == 1


def test_parse_date_valid_date_range() -> None:
    form = parse_form("Date = YYYY.MM.DD (today..)")()

    assert form['date'].label.text == 'Date'
    assert isinstance(form['date'], DateField)
    assert form['date'].widget.min == relativedelta()  # type: ignore[attr-defined]
    assert form['date'].widget.max is None  # type: ignore[attr-defined]
    assert len(form['date'].validators) == 2
    assert isinstance(form['date'].validators[1], ValidDateRange)
    assert form['date'].validators[1].min == relativedelta()
    assert form['date'].validators[1].max is None


def test_parse_datetime() -> None:
    form = parse_form("Datetime = YYYY.MM.DD HH:MM")()

    assert form['datetime'].label.text == 'Datetime'
    assert isinstance(form['datetime'], DateTimeLocalField)
    assert not hasattr(form['datetime'].widget, 'min')
    assert not hasattr(form['datetime'].widget, 'max')
    assert len(form['datetime'].validators) == 1


def test_parse_datetime_valid_date_range() -> None:
    form = parse_form("Datetime = YYYY.MM.DD HH:MM (..today)")()

    assert form['datetime'].label.text == 'Datetime'
    assert isinstance(form['datetime'], DateTimeLocalField)
    assert form['datetime'].widget.min is None  # type: ignore[attr-defined]
    assert form['datetime'].widget.max == relativedelta()  # type: ignore[attr-defined]
    assert len(form['datetime'].validators) == 2
    assert isinstance(form['datetime'].validators[1], ValidDateRange)
    assert form['datetime'].validators[1].min is None
    assert form['datetime'].validators[1].max == relativedelta()


def test_parse_time() -> None:
    form = parse_form("Time = HH:MM")()

    assert form['time'].label.text == 'Time'
    assert isinstance(form['time'], TimeField)


def test_parse_fileinput() -> None:
    form = parse_form("File = *.pdf|*.doc")()

    assert form['file'].label.text == 'File'
    assert isinstance(form['file'], FileField)
    assert form['file'].widget.multiple is False  # type: ignore[attr-defined]


def test_parse_multiplefileinput() -> None:
    form = parse_form("Files = *.pdf|*.doc (multiple)")()

    assert form['files'].label.text == 'Files'
    assert isinstance(form['files'], FileField)
    assert form['files'].widget.multiple is True  # type: ignore[attr-defined]


def test_parse_radio() -> None:

    text = dedent("""
        Gender =
            ( ) Male
            (x) Female
    """)

    form = parse_form(text)()

    assert len(form._fields) == 1
    assert isinstance(form['gender'], RadioField)
    assert form['gender'].choices == [
        ('Male', 'Male'),
        ('Female', 'Female'),
    ]
    assert form['gender'].default == 'Female'


def test_parse_radio_escape() -> None:

    text = dedent("""
        # "For sure"
        Let's go =
            ( ) Yeah, let's
            (x) No, let's not
    """)

    form = parse_form(text)()

    assert len(form._fields) == 1
    assert isinstance(form['for_sure_let_s_go'], RadioField)
    assert form['for_sure_let_s_go'].choices == [
        ("Yeah, let's", "Yeah, let's"),
        ("No, let's not", "No, let's not"),
    ]
    assert form['for_sure_let_s_go'].default == "No, let's not"


def test_parse_checkbox() -> None:

    text = dedent("""
        Extras =
            [ ] Extra Luggage
            [x] Priority Seating
            [x] Early Boarding
    """)

    form = parse_form(text)()

    assert len(form._fields) == 1
    assert isinstance(form['extras'], MultiCheckboxField)
    assert form['extras'].choices == [
        ('Extra Luggage', 'Extra Luggage'),
        ('Priority Seating', 'Priority Seating'),
        ('Early Boarding', 'Early Boarding'),
    ]
    assert form['extras'].default == ['Priority Seating', 'Early Boarding']


def test_parse_radio_with_pricing() -> None:

    text = dedent("""
        Drink =
            ( ) Coffee (2.50 CHF)
            (x) Tea (1.50 CHF!)
        << beer cant be cheaper than water >>
    """)

    form = parse_form(text)()
    assert form['drink'].pricing.rules == {
        'Coffee': Price(2.5, 'CHF'),
        'Tea': Price(1.5, 'CHF', credit_card_payment=True)
    }
    assert form['drink'].description == 'beer cant be cheaper than water'


def test_parse_checkbox_with_pricing() -> None:

    text = dedent("""
        Extras =
            [ ] Bacon (2.50 CHF!)
            [x] Cheese (1.50 CHF)
    """)

    form = parse_form(text)()
    assert form['extras'].pricing.rules == {
        'Bacon': Price(2.5, 'CHF', credit_card_payment=True),
        'Cheese': Price(1.5, 'CHF')
    }
    assert form['extras'].pricing.rules['Bacon'].amount == Decimal(2.5)
    assert form['extras'].pricing.rules['Bacon'].currency == 'CHF'
    assert form['extras'].pricing.rules['Bacon'].credit_card_payment is True


def test_parse_radio_with_discount() -> None:

    text = dedent("""
        Drink =
            ( ) Coffee (5%)
            (x) Tea (15%)
        << beer cant be cheaper than water >>
    """)

    form = parse_form(text)()
    assert form['drink'].discount == {
        'Coffee': Decimal('0.05'),
        'Tea': Decimal('0.15')
    }
    assert form['drink'].description == 'beer cant be cheaper than water'
    assert form.total_discount() == Decimal('0.15')


def test_parse_checkbox_with_discount() -> None:

    text = dedent("""
        Extras =
            [x] Bacon (-25%)
            [x] Cheese (75%)
    """)

    form = parse_form(text)()
    assert form['extras'].discount == {
        'Bacon': Decimal('-0.25'),
        'Cheese': Decimal('0.75')
    }
    assert form.total_discount() == Decimal('0.5')


def test_dependent_validation() -> None:

    text = dedent("""
        Payment * =
            ( ) Bill
                Address * = ___
                << Company preferred >>
            ( ) Credit Card
                Credit Card Number * = ___
    """)

    form_class = parse_form(text)
    assert len(form_class()._fields) == 3

    form = form_class(MultiDict([
        ('payment', 'Bill'),
        ('payment_address', 'Destiny Lane')
    ]))

    assert form['payment_address'].description == 'Company preferred'

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
        form['payment_address'].widget(
            form['payment_address'],
            **form['payment_address'].render_kw
        )
    )
    assert 'data-depends-on="payment/Credit Card"' in (
        form['payment_credit_card_number'].widget(
            form['payment_credit_card_number'],
            **form['payment_credit_card_number'].render_kw
        )
    )


def test_nested_regression() -> None:

    text = dedent("""
        Delivery * =
            (x) I want it delivered
                Alternate Address =
                    (x) No
                    ( ) Yes
                        Street = ___
                        << street >>
                        Town = ___
                        << town >>
                << Alt >>
            ( ) I want to pick it up
        << delivery >>
        Kommentar = ...
        << kommentar >>
    """)

    form_class = parse_form(text)

    form = form_class()

    assert len(form._fields) == 5
    assert isinstance(form['delivery'], RadioField)
    assert len(form['delivery'].choices) == 2
    assert isinstance(form['delivery_alternate_address'], RadioField)
    assert len(form['delivery_alternate_address'].choices) == 2

    assert hasattr(form, 'delivery_alternate_address_street')
    assert hasattr(form, 'delivery_alternate_address_town')
    assert form['kommentar'].description == 'kommentar'
    assert form['delivery'].description == 'delivery'
    assert form['delivery_alternate_address'].description == 'Alt'
    assert form['delivery_alternate_address_street'].description == 'street'
    assert form['delivery_alternate_address_town'].description == 'town'


def test_stdnum_field() -> None:

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
        parse_form("Invalid = # asdf")

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


def test_optional_date() -> None:

    text = "Date = YYYY.MM.DD"

    form_class = parse_form(text)

    form = form_class(MultiDict([
        ('date', '30.02.2015')
    ]))

    form.validate()
    assert form.errors == {'date': ['Not a valid date value.']}

    form = form_class(MultiDict([
        ('date', '')
    ]))

    form.validate()
    assert not form.errors


def test_date_valid_range_validation() -> None:

    text = "Date *= YYYY.MM.DD (2015.03.30..)"

    form_class = parse_form(text)

    form = form_class(MultiDict([
        ('date', '2015-03-29')
    ]))

    form.validate()
    assert form.errors == {
        'date': ['Needs to be on or after 30.03.2015.']
    }

    form = form_class(MultiDict([
        ('date', '2015-03-30')
    ]))

    form.validate()
    assert not form.errors


def test_date_valid_range_validation_between() -> None:

    text = "Date *= YYYY.MM.DD (2015.03.30..2016.03.30)"

    form_class = parse_form(text)

    form = form_class(MultiDict([
        ('date', '2015-03-29')
    ]))

    form.validate()
    assert form.errors == {
        'date': ['Needs to be between 30.03.2015 and 30.03.2016.']
    }

    form = form_class(MultiDict([
        ('date', '2016-03-30')
    ]))

    form.validate()
    assert not form.errors


def test_datetime_valid_range_validation() -> None:

    text = "Datetime *= YYYY.MM.DD HH:MM (..2015.03.30)"

    form_class = parse_form(text)

    form = form_class(MultiDict([
        ('datetime', '2015-03-31T00:00')
    ]))

    form.validate()
    assert form.errors == {
        'datetime': ['Needs to be on or before 30.03.2015.']
    }

    form = form_class(MultiDict([
        ('datetime', '2015-03-30T23:59')
    ]))

    form.validate()
    assert not form.errors


def test_invalid_syntax() -> None:
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


def test_parse_formcode() -> None:
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

    subfields = fieldsets[1].fields[0].choices[0].fields
    assert subfields is not None
    assert subfields[0].label == 'Type'
    assert subfields[0].id == 'order_products_type'
    assert hasattr(subfields[0], 'choices')
    assert subfields[0].choices[0].selected
    assert not subfields[0].choices[1].selected
    assert subfields[0].choices[0].label == 'Default'
    assert subfields[0].choices[1].label == 'Gluten-Free'


def test_parse_formcode_duplicate_fieldname() -> None:
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


def test_flatten_fieldsets() -> None:
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


def test_integer_range() -> None:

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

    # 0 should validate on a required field
    form_class = parse_form("Items *= 0..10")
    form = form_class(MultiDict([
        ('items', '0')
    ]))

    form.validate()
    assert not form.errors


def test_integer_range_with_pricing() -> None:

    form_class = parse_form("Stamps = 0..20 (1.00 CHF)")
    form = form_class(MultiDict([
        ('stamps', '')
    ]))
    form.validate()
    assert not form.errors
    assert form['stamps'].pricing.rules == {
        range(0, 20): Price(Decimal('1.00'), 'CHF'),
    }
    assert not form['stamps'].pricing.has_payment_rule
    assert form['stamps'].pricing.price(form['stamps']) is None

    form = form_class(MultiDict([
        ('stamps', '0')
    ]))
    form.validate()
    assert not form.errors
    # special case: we don't want `Price(0, 'CHF')` since the
    # price might be flagged, which we don't want
    assert form['stamps'].pricing.price(form['stamps']) is None

    form = form_class(MultiDict([
        ('stamps', '10')
    ]))
    form.validate()
    assert not form.errors
    assert form['stamps'].pricing.price(form['stamps']) == Price(10.00, 'CHF')

    form_class = parse_form("Stamps *= 0..20 (1.00 CHF!)")
    form = form_class(MultiDict([
        ('stamps', '20')
    ]))
    form.validate()
    assert not form.errors
    assert form['stamps'].pricing.rules == {
        range(0, 20): Price(Decimal('1.00'), 'CHF', credit_card_payment=True),
    }
    assert form['stamps'].pricing.has_payment_rule
    assert form['stamps'].pricing.price(form['stamps']) == Price(
        20.00, 'CHF', credit_card_payment=True
    )


def test_decimal_range() -> None:

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

    # 0 should validate on a decimal field
    form_class = parse_form("Percentage = 0.00..100.00")
    form = form_class(MultiDict([
        ('percentage', '0.0')
    ]))

    form.validate()
    assert not form.errors


def test_field_ids() -> None:
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
    assert hasattr(fs[1].fields[0], 'choices')
    subfields = fs[1].fields[0].choices[0].fields
    assert subfields is not None
    assert subfields[0].id == 'my_order_products_type'
    assert subfields[0].human_id == 'My Order/Products/Type'

    assert find_field(fs, None) is fs[0]
    assert find_field(fs, 'my_order') is fs[1]
    assert find_field(fs, 'My Order') is fs[1]
    assert find_field(fs, 'first_name').id == 'first_name'  # type: ignore[union-attr]
    assert find_field(fs, 'First Name').id == 'first_name'  # type: ignore[union-attr]
    assert find_field(fs, 'last_name').id == 'last_name'  # type: ignore[union-attr]
    assert find_field(fs, 'Last Name').id == 'last_name'  # type: ignore[union-attr]
    assert find_field(fs, 'my_order_products').id == 'my_order_products'  # type: ignore[union-attr]
    assert find_field(fs, 'My Order/Products').id == 'my_order_products'  # type: ignore[union-attr]
    assert find_field(  # type: ignore[union-attr]
        fs, 'my_order_products_type'
    ).id == 'my_order_products_type'
    assert find_field(  # type: ignore[union-attr]
        fs, 'My Order/Products/Type'
    ).id == 'my_order_products_type'

    assert fs[0].find_field('first_name').id == 'first_name'  # type: ignore[union-attr]
    assert fs[0].find_field('First Name').id == 'first_name'  # type: ignore[union-attr]
    assert fs[1].find_field('first_name') is None
    assert fs[1].find_field('First Name') is None


@pytest.mark.parametrize("field,invalid", [
    ('@@@', 'foo'),
    ('0..99', 100),
    ('0.00..99.99', 100.00),
    ('# iban', 'foo')
])
def test_dependency_validation_chain(field: str, invalid: object) -> None:
    for required in (True, False):
        code = """
            select *=
                ( ) ya
                    value {}= {}
                (x) no
        """.format(required and '*' or '', field)

        form = parse_form(code)

        # we cannot supply an empty value if the dependency is fulfilled
        # and an input is required
        if required:
            assert not form(data={'select': 'ya'}).validate()

        # we can supply an empty value if the dependency is not fulfilled
        assert form(data={'select': 'no'}).validate()

        # we cannot supply an invalid value in any case
        inv = invalid
        assert not form(data={'select': 'no', 'select_value': inv}).validate()
        assert not form(data={'select': 'ya', 'select_value': inv}).validate()


def test_parse_dependency_with_price() -> None:
    text = dedent(
        """
    Versand *=
        ( ) Ich möchte die Bestellung am Schalter abholen
        (x) Ich möchte die Bestellung mittels Post erhalten (5 CHF)
            Strasse (inkl. Hausnummer) *= ___
            PLZ / Ort *= ___
    """
    )

    fieldsets = parse_formcode(text)
    assert len(fieldsets) == 1
    assert fieldsets[0].fields[0].type == "radio"
    assert len(fieldsets[0].fields) == 1

    from onegov.form.parser.core import RadioField

    assert isinstance(fieldsets[0].fields[0], RadioField)
    choices = fieldsets[0].fields[0].choices
    assert len(choices) == 2


@pytest.mark.parametrize('indent,edit_checks,shall_raise', [
    # indent check active while parsing
    ('', True, False),
    (' ', True, True),
    ('  ', True, True),
    ('   ', True, True),
    # no indent check while parsing
    ('', False, False),
])
def test_indentation_error(
    indent: str,
    edit_checks: bool,
    shall_raise: bool
) -> None:
    # wrong indent see 'Telefonnummer'
    text = dedent(
        """
        # Kiosk
        Name des Kiosks = ___
        # Kontaktangaben
        Kontaktperson = ___
        {}Telefonnummer = ___
        """.format(indent)
    )

    if shall_raise:
        with pytest.raises(InvalidIndentSyntax) as excinfo:
            parse_formcode(text, enable_edit_checks=edit_checks)

        assert excinfo.value.line == 6
    else:
        assert parse_formcode(text, enable_edit_checks=edit_checks)


def test_help_indentation_error() -> None:
    text = dedent(
        """
        Contact person *= ___
        << Name of the contact person >>
        Favorit fruit =
            ( ) Apple
            ( ) Banana
        << Please select your favorit fruit >>
        """
    )
    assert parse_formcode(text, enable_edit_checks=True)

    text = dedent(
        """
        Contact person = ___
            << Name of the contact person >>
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentIndentSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
        assert excinfo.value.line == 2

    text = dedent(
        """
        Email *= @@@
        << Put your personal email >>

        Contact person = ___
            << Name of the contact person >>
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentIndentSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
        assert excinfo.value.line == 5

    text = dedent(
        """
        Email *= @@@
        << Put your personal email >>
        Name = ___

        Terms of Use / User Agreement *=
            ( ) I accept the Terms of Use / User Agreement
            << Please find the terms attached below .. >>
            ( ) I DONT accept the Terms of Use / User Agreement
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentIndentSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 7

    text = dedent(
        """
        Email *= @@@

        Preferred Sports =
            [ ] Baseball
            [ ] Football
            [ ] Skiing
            << Please select all your preferred sports >>
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentIndentSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 7

    text = dedent(
        """
        Email *= @@@
        Preferred Sports =
            [ ] Baseball
            [ ] Football
            [ ] Skiing
        << Please select all your preferred sports >>
        Name *= ___
            << Please enter your name >>
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentIndentSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 8


    text = dedent(
        """
        Email *= @@@
        Want Condiments =
            (x) Yes
                condiments =
                    [ ] Relish
                    [ ] Jalapenos
                    [ ] Ketchup
                    [ ] Other
                        What else? = ___
                << Choose your favorite condiments >>
            ( ) No Condiments
        << Whether or not you want condiments in your hotdog? >>
        Name *= ___
            << Please enter your name >>
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentIndentSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 14


    text = dedent(
        """
        Email *= @@@
        Want Condiments =
            (x) Yes
                Condiments =
                    [ ] Relish
                    [ ] Jalapenios
                    [ ] Ketchup
                    [ ] Other
                        What else? = ___
                << Choose your favorite condiments >>
            ( ) No Condiments
        << Whether or not you want condiments in your hotdog? >>
        Dessert =
            ( ) Yes
                Desserts =
                    ( ) Ice Cream
                    ( ) Cookie
                    << badly indented >>
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentIndentSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 18


def test_help_location_error() -> None:
    text = dedent(
        """
        Email *= @@@
        << Put your personal email >>
        Terms of Use / User Agreement *=
            ( ) I accept the Terms of Use / User Agreement
        << Please find the terms attached below .. >>
        """
    )
    assert parse_formcode(text, enable_edit_checks=True)

    text = dedent(
        """
        # Comment
        << Put your personal email >>
        Email *= @@@
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentLocationSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 2

    text = dedent(
        """
        Email *= @@@
        << Put your personal email >>

        Terms of Use / User Agreement *=
        << Please find the terms attached below .. >>
            ( ) I accept the Terms of Use / User Agreement
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentLocationSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 5

    text = dedent(
        """
        Email *= @@@
        << Put your personal email >>
        Name = ___

        Terms of Use / User Agreement *=
        << Please find the terms attached below .. >>
            ( ) I accept the Terms of Use / User Agreement
        """
    ).lstrip('\n')
    with pytest.raises(InvalidCommentLocationSyntax) as excinfo:
        parse_formcode(text, enable_edit_checks=True)
    assert excinfo.value.line == 6


def test_empty_fieldset_error() -> None:
    fieldsets = parse_formcode('\n'.join((
        "# Section 1",
        "# Section 2",
        "First Name *= ___",
        "Last Name *= ___",
        "E-mail *= @@@"
    )), enable_edit_checks=False)
    assert len(fieldsets) == 2

    with pytest.raises(errors.EmptyFieldsetError) as e:
        parse_formcode('\n'.join((
            "# Section 1",
            "# Section 2",
            "First Name *= ___",
            "Last Name *= ___",
            "E-mail *= @@@"
        )), enable_edit_checks=True)

    assert e.value.field_name == 'Section 1'

    with pytest.raises(errors.EmptyFieldsetError) as e:
        parse_formcode('\n'.join((
            "# Section 1",
            "First Name *= ___",
            "Last Name *= ___",
            "# Section 2",
            "E-mail *= @@@",
            "# Section 3",
        )), enable_edit_checks=True)

    assert e.value.field_name == 'Section 3'

    with pytest.raises(errors.EmptyFieldsetError) as e:
        parse_formcode('\n'.join((
            "# Section 1",
            "First Name *= ___",
            "Last Name *= ___",
            "# Section 2",
            "# Section 3",
            "E-mail *= @@@",
        )), enable_edit_checks=True)

    assert e.value.field_name == 'Section 2'
