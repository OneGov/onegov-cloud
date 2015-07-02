from onegov.form import Form, with_options
from wtforms import StringField, TextAreaField, validators
from wtforms.fields.html5 import EmailField
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
        test = StringField("Test", [validators.DataRequired()])

    request = DummyRequest({})
    assert not TestForm(request.POST).submitted(request)

    request = DummyRequest({'test': 'Test'})
    assert TestForm(request.POST).submitted(request)


def test_useful_data():

    class TestForm(Form):
        a = StringField("a")
        b = StringField("b")
        c = StringField("c")

    request = DummyRequest({'a': 'A', 'b': 'B', 'c': 'C'})
    assert TestForm(request.POST).get_useful_data(exclude={'a', 'b'}) \
        == {'c': 'C'}


def test_with_options():
    widget = with_options(TextArea, class_="markdown")
    assert 'class="markdown"' in widget(DummyField('one', 'one', '1'))

    widget = with_options(TextArea, class_="x")
    assert 'class="x"' in widget(DummyField('one', 'one', '1'))


def test_match_fields():

    class TestForm(Form):
        name = StringField("Name", [validators.DataRequired()])
        email = EmailField("E-Mail")
        comment = TextAreaField("Comment")

    form = TestForm()
    assert form.match_fields(required=True) == ['name']
    assert form.match_fields(required=False) == ['email', 'comment']
    assert form.match_fields(required=None) == ['name', 'email', 'comment']
    assert form.match_fields(required=None, limit=1) == ['name']
    assert form.match_fields(include_classes=(StringField, ))\
        == ['name', 'email', 'comment']
    assert form.match_fields(include_classes=(EmailField, )) == ['email']
    assert form.match_fields(exclude_classes=(TextAreaField, ))\
        == ['name', 'email']
