from onegov.gazette.collections import CategoryCollection
from onegov.gazette.validators import UnusedColumnKeyValue
from onegov.notice import OfficialNotice
from onegov.notice import OfficialNoticeCollection
from pytest import raises
from wtforms.validators import ValidationError


class DummyApp(object):
    def __init__(self, session):
        self._session = session

    def session(self):
        return self._session


class DummyRequest(object):
    def __init__(self, session):
        self.app = DummyApp(session)
        self.session = session


class DummyForm(object):
    def __init__(self, session):
        self.request = DummyRequest(session)


class DummyField(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data


def test_unused_column_key_value_validator(session):
    # new item
    form = DummyForm(session)
    field = DummyField('name', 'XXX')
    validator = UnusedColumnKeyValue(OfficialNotice._categories)
    validator(form, field)

    # used value
    OfficialNoticeCollection(session).add('title', 'text', categories=['1'])
    form.model = CategoryCollection(session).add_root(title='XXX')
    assert form.model.name == '1'
    with raises(ValidationError) as excinfo:
        validator(form, field)
    assert str(excinfo.value) == 'This value is in use.'
