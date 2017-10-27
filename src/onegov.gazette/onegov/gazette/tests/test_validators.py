from onegov.user import UserCollection
from onegov.gazette.validators import UniqueColumnValue
from pytest import raises
from wtforms.validators import ValidationError
from onegov.user import User


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
    def __init__(self, data):
        self.data = data


def test_unique_column_value_validator(session):
    form = DummyForm(session)
    field = DummyField('a@example.org')
    validator = UniqueColumnValue(User.username)

    validator(form, field)

    UserCollection(session).add('a@example.org', 'pwd', 'editor')
    with raises(ValidationError) as excinfo:
        validator(form, field)
    assert str(excinfo.value) == 'This value already exists.'

    validator = UniqueColumnValue(User.username, message='message')
    with raises(ValidationError) as excinfo:
        validator(form, field)
    assert str(excinfo.value) == 'message'

    form.old_field = DummyField('a@example.org')
    validator = UniqueColumnValue(User.username, old_field='old_field')
