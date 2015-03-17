from onegov.form import Form
from wtforms import StringField, validators


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


class DummyRequest(object):
    def __init__(self, POST):
        self.POST = DummyPostData(POST)


def test_submitted():

    class TestForm(Form):
        test = StringField("Test", [validators.InputRequired()])

    request = DummyRequest({})
    assert not TestForm(request.POST).submitted(request)

    request = DummyRequest({'test': 'Test'})
    assert TestForm(request.POST).submitted(request)
