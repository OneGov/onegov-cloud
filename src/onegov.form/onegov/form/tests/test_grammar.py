# -*- coding: utf-8 -*-
import textwrap

from onegov.form.parser.grammar import (
    button,
    custom,
    document,
    field_identifier,
    checkboxes,
    password,
    textarea,
    textfield,
    radios,
    text_without,
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


def test_radios():

    field = radios()

    f = field.parseString("( ) Male (x) Female ( ) Space Alien")
    assert f.type == 'radio'

    assert [r.asDict() for r in f] == [
        {'checked': False, 'label': 'Male'},
        {'checked': True, 'label': 'Female'},
        {'checked': False, 'label': 'Space Alien'}
    ]

    f = field.parseString("( ) Hans ")

    assert [r.asDict() for r in f] == [
        {'checked': False, 'label': 'Hans'},
    ]


def test_checkboxes():

    field = checkboxes()

    f = field.parseString("[x] German [ ] English [ ] Swiss German ")
    assert f.type == 'checkbox'

    assert [r.asDict() for r in f] == [
        {'checked': True, 'label': 'German'},
        {'checked': False, 'label': 'English'},
        {'checked': False, 'label': 'Swiss German'}
    ]


def test_custom():

    field = custom()

    f = field.parseString("/E-Mail")
    assert f.asDict() == {'type': 'custom', 'custom_id': 'e-mail'}

    f = field.parseString("/Stripe")
    assert f.asDict() == {'type': 'custom', 'custom_id': 'stripe'}


def test_button():

    btn = button()

    f = btn.parseString("[Click Me!](https://www.google.ch)")
    assert f.asDict() == {
        'type': 'button',
        'label': 'Click Me!',
        'url': 'https://www.google.ch'
    }

    f = btn.parseString("[Send]")
    assert f.asDict() == {
        'type': 'button',
        'label': 'Send'
    }


def test_document():
    # a form that includes all the features available
    form = textwrap.dedent("""
        # Name

        First name* = ___
        Last name* = ___[50]

        # Delivery

        Delivery Method =
            ( ) Pickup
            (x) Postal Service

        # ...

        Payment* = ( ) Bill (x) Credit Card
        Password = ***
        Comment = ...
        E-Mail = /E-Mail

        [Submit](https://www.google.ch)
    """)

    result = document().searchString(form)
    assert len(result) == 11

    assert result[0].asDict() == {'label': 'Name', 'type': 'fieldset'}

    assert result[1].asDict() == {
        'label': 'First name',
        'type': 'text',
        'required': True
    }
    assert result[2].asDict() == {
        'label': 'Last name',
        'type': 'text',
        'required': True,
        'length': 50
    }

    assert result[3].asDict() == {'label': 'Delivery', 'type': 'fieldset'}

    assert result[4]['label'] == 'Delivery Method'
    assert result[4]['type'] == 'radio'
    assert not result[4]['required']

    assert result[4]['parts'][0].asDict() == {
        'checked': False, 'label': 'Pickup'
    }

    assert result[4]['parts'][1].asDict() == {
        'checked': True, 'label': 'Postal Service'
    }

    assert result[5].asDict() == {'type': 'fieldset'}

    assert result[6]['label'] == 'Payment'
    assert result[6]['type'] == 'radio'
    assert result[6]['required']

    assert result[6]['parts'][0].asDict() == {
        'checked': False, 'label': 'Bill'
    }

    assert result[6]['parts'][1].asDict() == {
        'checked': True, 'label': 'Credit Card'
    }

    assert result[7].asDict() == {
        'required': False, 'label': 'Password', 'type': 'password'
    }
    assert result[8].asDict() == {
        'required': False, 'label': 'Comment', 'type': 'textarea'
    }
    assert result[9].asDict() == {
        'required': False,
        'label': 'E-Mail',
        'type': 'custom',
        'custom_id': 'e-mail'
    }
    assert result[10].asDict() == {
        'label': 'Submit',
        'type': 'button',
        'url': 'https://www.google.ch'
    }


def test_multiline_checkboxes():
    form = textwrap.dedent("""
        # Extras

        Extras = [ ] Priority Boarding
                 [ ] Extra Luggage
                 [x] Travel Insurance

    """)

    result = document().searchString(form)
    assert len(result) == 2

    assert result[0].asDict() == {'label': 'Extras', 'type': 'fieldset'}

    assert result[1]['label'] == 'Extras'
    assert result[1]['type'] == 'checkbox'
    assert not result[1]['required']

    assert result[1]['parts'][0].asDict() == {
        'checked': False, 'label': 'Priority Boarding'
    }

    assert result[1]['parts'][1].asDict() == {
        'checked': False, 'label': 'Extra Luggage'
    }

    assert result[1]['parts'][2].asDict() == {
        'checked': True, 'label': 'Travel Insurance'
    }


def test_nested_blocks():
    form = textwrap.dedent("""
        Payment = (x) Bill
                  ( ) Credit Card
                      Address = ___

    """)
    result = document().searchString(form)

    assert len(result) == 1
    assert result[0].parts[1].dependencies[0].asDict() == {
        'required': False, 'label': 'Address', 'type': 'text'
    }


def test_nested_nested():
    form = textwrap.dedent("""
        Payment = (x) Bill
                      Address = ___
                      Comment = ...

                  ( ) Credit Card
                      Type = (x) Visa
                             ( ) Mastercard
                      Store = [ ] Address
                              [x] Card

    """)
    result = document().searchString(form)

    assert len(result) == 1
    assert result[0].parts[0].dependencies[0].asDict() == {
        'label': 'Address', 'required': False, 'type': 'text'
    }
    assert result[0].parts[0].dependencies[1].asDict() == {
        'label': 'Comment', 'required': False, 'type': 'textarea'
    }
    assert result[0].parts[1].dependencies[0].label == 'Type'
    assert result[0].parts[1].dependencies[0].type == 'radio'
    assert result[0].parts[1].dependencies[0].parts[0].asDict() == {
        'checked': True, 'label': 'Visa'
    }
    assert result[0].parts[1].dependencies[0].parts[1].asDict() == {
        'checked': False, 'label': 'Mastercard'
    }
    assert result[0].parts[1].dependencies[1].parts[0].asDict() == {
        'checked': False, 'label': 'Address'
    }
    assert result[0].parts[1].dependencies[1].parts[1].asDict() == {
        'checked': True, 'label': 'Card'
    }


def test_nested_nested_nested():
    form = textwrap.dedent("""
        Delivery = (x) Pickup
                   ( ) Fedex
                       Address = (x) Postbox
                                     Postbox Number = ___
                                 ( ) Home Address
                                     Street = ___
    """)
    result = document().searchString(form)

    assert result[0].parts[0].asDict() == {'checked': True, 'label': 'Pickup'}
    assert result[0].parts[1].label == 'Fedex'

    address = result[0].parts[1].dependencies[0]

    assert address.label == 'Address'
    assert address.parts[0].label == 'Postbox'
    assert address.parts[0].checked
    assert address.parts[1].label == 'Home Address'
    assert not address.parts[1].checked

    assert address.parts[0].dependencies[0].label == 'Postbox Number'
    assert address.parts[1].dependencies[0].label == 'Street'
