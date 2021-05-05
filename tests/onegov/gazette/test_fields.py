from onegov.form import Form
from onegov.gazette.fields import MultiCheckboxField


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_multi_checkbox_field():
    form = Form()
    field = MultiCheckboxField(choices=(('a', 'b'),))
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'data-expand-title="Show all"' in field()
    assert 'data-fold-title="Show less"' in field()
    assert 'data-limit="5"' in field()
