from onegov.core.custom import json
from onegov.user.auth import Auth
from onegov.user.collections import UserCollection
from onegov.user.forms import LoginForm
from onegov.user.forms import PasswordResetForm
from onegov.user.forms import RegistrationForm
from onegov.user.forms import RequestPasswordResetForm
from onegov.user.forms import UserGroupForm
from onegov.user.models import User
from onegov.user.models import UserGroup


class DummyApp():
    def __init__(self, session):
        self._session = session

    def session(self):
        return self._session


class DummyRequest():
    def __init__(self, session):
        self.app = DummyApp(session)
        self.client_addr = '127.0.0.1'
        self.session = session

    def load_url_safe_token(self, token, **kwargs):
        if not token:
            return None

        return json.loads(token)


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def test_login_form():
    # Test validation
    form = LoginForm()
    assert not form.validate()

    form.process(DummyPostData({
        'username': 'info@example.com',
        'password': 'much_secret'
    }))
    assert form.validate()
    assert form.login_data == {
        'username': 'info@example.com',
        'password': 'much_secret',
        'second_factor': None,
    }

    form.process(DummyPostData({
        'username': 'info@example.com',
        'password': 'much_secret',
        'yubikey': 'abcdefghijklmnopqrstuvwxyz'
    }))
    assert form.validate()
    assert form.login_data == {
        'username': 'info@example.com',
        'password': 'much_secret',
        'second_factor': 'abcdefghijklmnopqrstuvwxyz',
    }


def test_registration_form(session):
    # Test validation
    form = RegistrationForm()
    assert not form.validate()

    form.process(DummyPostData({
        'username': 'info@example.com',
        'password': 'much_secret',
        'confirm': 'very_secret'
    }))
    assert not form.validate()

    form.process(DummyPostData({
        'username': 'info@example.com',
        'password': 'much_secret',
        'confirm': 'much_secret',
        'roboter_falle': 'fooled'
    }))
    assert not form.validate()

    form.process(DummyPostData({
        'username': 'info@example.com',
        'password': 'much_secret',
        'confirm': 'much_secret'
    }))
    assert form.validate()

    # Test register user
    auth = Auth(session, 'foobar')
    auth.register(form, DummyRequest(session))

    assert session.query(User).filter_by(username='info@example.com').one()


def test_request_password_reset_form():
    # Test validation
    form = RequestPasswordResetForm()
    assert not form.validate()

    form.process(DummyPostData({
        'email': 'name',
    }))
    assert not form.validate()

    form.process(DummyPostData({
        'email': 'info@example.com',
    }))
    assert form.validate()


def test_password_reset_form(session):
    # Test validation
    request = DummyRequest(session)
    form = PasswordResetForm()
    assert not form.validate()

    form.process(DummyPostData({
        'email': 'name',
        'password': 'secret',
    }))
    assert not form.validate()

    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'secret',
    }))
    assert not form.validate()

    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
    }))
    assert form.validate()
    assert not form.update_password(request)

    # Test update password
    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
        'token': json.dumps({'username': 'username'})
    }))
    assert form.validate()
    assert not form.update_password(request)

    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
        'token': json.dumps({'username': 'info@example.com'})
    }))
    assert form.validate()
    assert not form.update_password(request)

    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
        'token': json.dumps({'username': 'info@example.com'})
    }))
    assert form.validate()
    assert not form.update_password(request)

    assert UserCollection(session).register(
        'info@example.com', 'very_secret', request
    )
    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
        'token': json.dumps({'username': 'info@example.com'})
    }))
    assert form.validate()
    assert not form.update_password(request)

    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
        'token': json.dumps({
            'username': 'info@example.com',
            'modified': 'now'
        })
    }))
    assert form.validate()
    assert not form.update_password(request)

    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
        'token': json.dumps({
            'username': 'info@example.com',
            'modified': ''
        })
    }))
    assert form.validate()
    assert form.update_password(request)

    form.process(DummyPostData({
        'email': 'info@example.com',
        'password': 'much_secret',
        'token': json.dumps({
            'username': 'info@example.com',
            'modified': ''
        })
    }))
    assert form.validate()
    assert not form.update_password(request)


def test_user_group_form():
    # Test apply / update
    form = UserGroupForm()
    group = UserGroup(name='Group X')

    form.apply_model(group)
    assert form.name.data == 'Group X'

    form.name.data = 'Group Y'
    form.update_model(group)
    assert group.name == 'Group Y'

    # Test validation
    form = UserGroupForm()
    assert not form.validate()

    form = UserGroupForm(DummyPostData({'name': 'Group'}))
    assert form.validate()
