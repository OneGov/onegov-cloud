from onegov.form import Form
from onegov.gazette.fields import MultiCheckboxField
from onegov.gazette.fields import SelectField


def test_select_field():
    form = Form()
    field = SelectField(choices=(('a', 'b'),))
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'class="chosen-select"' in field()


def test_multi_checkbox_field():
    form = Form()
    field = MultiCheckboxField(choices=(('a', 'b'),))
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'data-expand-title="Show all"' in field()
    assert 'data-limit="10"' in field()
