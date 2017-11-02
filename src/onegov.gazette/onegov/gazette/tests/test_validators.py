from onegov.gazette.collections import CategoryCollection
from onegov.gazette.validators import UniqueColumnValue
from onegov.gazette.validators import UnusedColumnKeyValue
from onegov.notice import OfficialNotice
from onegov.notice import OfficialNoticeCollection
from onegov.user import User
from onegov.user import UserCollection
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


class DummyForm(object):
    def __init__(self, session):
        self.request = DummyRequest(session)


class DummyField(object):
    def __init__(self, name, data):
        self.name = name
        self.data = data


def test_unique_column_value_validator(session):
    # new item
    form = DummyForm(session)
    field = DummyField('username', 'a@example.org')
    validator = UniqueColumnValue(User)
    validator(form, field)

    # existing value
    user = UserCollection(session).add('a@example.org', 'pwd', 'editor')
    with raises(ValidationError) as excinfo:
        validator(form, field)
    assert str(excinfo.value) == 'This value already exists.'

    # provide a default
    form.model = user
    validator(form, field)


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
