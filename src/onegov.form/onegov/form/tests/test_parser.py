import pytest

from onegov.form.parser import parse_form
from textwrap import dedent
from wtforms.fields.html5 import EmailField


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

    assert form.last_name.label.text == 'Last name'
    assert len(form.last_name.validators) == 0

    assert form.country.label.text == 'Country'
    assert len(form.country.validators) == 1

    assert form.comment.label.text == 'Comment'
    assert form.comment.widget(form.comment) == (
        '<textarea id="comment" name="comment" rows="8"></textarea>')


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
    assert fieldsets[0]['first_name'].label.text == 'First name'
    assert fieldsets[0]['last_name'].label.text == 'Last name'

    assert len(fieldsets[1]) == 1
    assert fieldsets[1].label == 'Address'
    assert fieldsets[1].is_visible
    assert fieldsets[1]['street'].label.text == 'Street'

    assert len(fieldsets[2]) == 1
    assert fieldsets[2].label is None
    assert not fieldsets[2].is_visible
    assert fieldsets[2]['comment'].label.text == 'Comment'


def test_parse_custom_fields():

    with pytest.raises(NotImplementedError):
        form = parse_form("E-Mail = /E-Mail")

    form = parse_form("E-Mail = /E-Mail", custom_fields={
        'e-mail': EmailField
    })()

    assert form.e_mail.label.text == 'E-Mail'
    assert isinstance(form.e_mail, EmailField)
