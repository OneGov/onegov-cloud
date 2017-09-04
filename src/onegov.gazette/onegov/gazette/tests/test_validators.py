from onegov.user import UserCollection
from onegov.gazette.validators import UniqueUsername
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
    def __init__(self, data):
        self.data = data


def test_unique_username_validator(session):
    form = DummyForm(session)
    field = DummyField('a@example.org')
    validator = UniqueUsername()

    validator(form, field)

    UserCollection(session).add('a@example.org', 'pwd', 'editor')
    with raises(ValidationError):
        validator(form, field)

    form.default_field = DummyField('a@example.org')
    validator = UniqueUsername(default_field='default_field')
