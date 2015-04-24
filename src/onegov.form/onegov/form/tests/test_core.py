from onegov.form import Form, with_options
from wtforms import StringField, validators
from wtforms.widgets import TextArea


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


class DummyRequest(object):
    def __init__(self, POST):
        self.POST = DummyPostData(POST)


class DummyField(object):
    def __init__(self, id, name, value):
        self.id = id
        self.name = name
        self.value = value

    def _value(self):
        return self.value


def test_submitted():

    class TestForm(Form):
        test = StringField("Test", [validators.InputRequired()])

    request = DummyRequest({})
    assert not TestForm(request.POST).submitted(request)

    request = DummyRequest({'test': 'Test'})
    assert TestForm(request.POST).submitted(request)


def test_with_options():
    widget = with_options(TextArea, class_="markdown")
    assert 'class="markdown"' in widget(DummyField('one', 'one', '1'))

    widget = with_options(TextArea, class_="x")
    assert 'class="x"' in widget(DummyField('one', 'one', '1'))
