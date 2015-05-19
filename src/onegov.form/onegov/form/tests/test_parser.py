from onegov.form.parser import parse_form
from textwrap import dedent


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
