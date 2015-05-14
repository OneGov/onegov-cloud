# -*- coding: utf-8 -*-
import textwrap

from onegov.form.parser.grammar import (
    block_content,
    button,
    custom,
    document,
    field_identifier,
    checkboxes,
    password,
    select,
    textarea,
    textfield,
    radios,
)


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

    f = field.parseString("() Male (x) Female ( ) Space Alien")
    assert f.type == 'radio'

    assert [r.asDict() for r in f] == [
        {'checked': False, 'label': 'Male'},
        {'checked': True, 'label': 'Female'},
        {'checked': False, 'label': 'Space Alien'}
    ]

    f = field.parseString("() Hans ")

    assert [r.asDict() for r in f] == [
        {'checked': False, 'label': 'Hans'},
    ]


def test_checkboxes():

    field = checkboxes()

    f = field.parseString("[x] German [ ] English [] Swiss German ")
    assert f.type == 'checkbox'

    assert [r.asDict() for r in f] == [
        {'checked': True, 'label': 'German'},
        {'checked': False, 'label': 'English'},
        {'checked': False, 'label': 'Swiss German'}
    ]


def test_select():

    field = select()

    f = field.parseString("{KUL, ZRH, (DXB)}")
    assert f.type == 'select'

    assert [s.asDict() for s in f] == [
        {'selected': False, 'label': 'KUL'},
        {'selected': False, 'label': 'ZRH'},
        {'selected': True, 'label': 'DXB'}
    ]

    f = field.parseString("{KUL, ZRH > Zürich, (DXB > Dubai)}")

    assert [s.asDict() for s in f] == [
        {'selected': False, 'label': 'KUL'},
        {'selected': False, 'label': 'Zürich', 'key': 'ZRH'},
        {'selected': True, 'label': 'Dubai', 'key': 'DXB'}
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
    """)

    result = document().searchString(form)
    assert result[0].asDict() == {
        'label': 'First name',
        'type': 'text',
        'required': True
    }
    assert result[1].asDict() == {
        'label': 'Last name',
        'type': 'text',
        'required': True,
        'length': 50
    }
    result[2]['label'] == 'Delivery Method'
    result[2]['type'] == 'radio'
    result[2]['required'] == 'False'

    result[2]['parts'][0].asDict() == {
        'checked': False, 'label': 'Pickup'
    }
    result[2]['parts'][0].asDict() == {
        'checked': True, 'label': 'Postal Service'
    }
