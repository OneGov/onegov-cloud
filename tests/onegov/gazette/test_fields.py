from datetime import datetime
from onegov.form import Form
from onegov.gazette.fields import DateTimeLocalField
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

    form = Form()
    field = MultiCheckboxField(
        choices=(('a', 'b'),),
        render_kw={'disabled': True}
    )
    field = field.bind(form, 'choice')

    field.data = ''
    assert 'input disabled' in field()


def test_date_time_local_field():
    form = Form()
    field = DateTimeLocalField()
    field = field.bind(form, 'dt')

    assert field.format == '%Y-%m-%dT%H:%M'
    field.data = datetime(2010, 1, 2, 3, 4)
    assert "2010-01-02T03:04" in field()

    field = DateTimeLocalField()
    field = field.bind(form, 'dt')

    field.process(DummyPostData({'dt': "2010-01-02T03:04"}))
    assert field.data == datetime(2010, 1, 2, 3, 4)

    field.process(DummyPostData({'dt': "2010-05-06 07:08"}))
    assert field.data == datetime(2010, 5, 6, 7, 8)
