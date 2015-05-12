# -*- coding: utf-8 -*-
from onegov.form.parser.grammar import field_declaration, field, line


def test_field_declaration():
    parse = field_declaration().parseString

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

    f = field.parseString("Vorname = ___")
    assert f.label == "Vorname"
    assert not f.required
    assert f.field.type == 'text'
    assert f.field.length == ''

    f = field.parseString("Vorname* = ___[25]")
    assert f.label == "Vorname"
    assert f.required
    assert f.field.type == 'text'
    assert f.field.length == 25


def test_radiobutton():

    f = field.parseString("Gender* = () Male (x) Female")
    assert f.label == "Gender"
    assert f.required
    assert f.field.type == 'radio'
    assert f.field[0].label == 'Male'
    assert not f.field[0].checked
    assert f.field[1].label == 'Female'
    assert f.field[1].checked


def test_checkboxes():

    f = field.parseString("Languages = [x] German [x] English [] French")
    assert f.label == "Languages"
    assert not f.required
    assert f.field.type == 'checkbox'
    assert f.field[0].label == 'German'
    assert f.field[0].checked
    assert f.field[1].label == 'English'
    assert f.field[1].checked
    assert f.field[2].label == 'French'
    assert not f.field[2].checked


def test_select():

    f = field.parseString("Airports = {KUL, ZRH, (DXB)}")
    assert f.label == "Airports"
    assert not f.required

    assert f.field.type == 'select'
    assert f.field[0].key == ''
    assert f.field[0].label == 'KUL'
    assert not f.field[0].selected
    assert f.field[1].key == ''
    assert f.field[1].label == 'ZRH'
    assert not f.field[1].selected
    assert f.field[2].key == ''
    assert f.field[2].label == 'DXB'
    assert f.field[2].selected

    f = field.parseString("Airports = {KUL, ZRH > Zürich, (DXB > Dubai)}")
    assert f.label == "Airports"
    assert not f.required

    assert f.field.type == 'select'
    assert f.field[0].key == ''
    assert f.field[0].label == 'KUL'
    assert not f.field[0].selected
    assert f.field[1].key == 'ZRH'
    assert f.field[1].label == 'Zürich'
    assert not f.field[1].selected
    assert f.field[2].key == 'DXB'
    assert f.field[2].label == 'Dubai'
    assert f.field[2].selected


def test_fieldset_title():

    f = line.parseString("# My Title")
    assert f.type == 'fieldset'
    assert f.label == 'My Title'

    f = line.parseString("#")
    assert f.type == 'fieldset'
    assert f.label == ''
