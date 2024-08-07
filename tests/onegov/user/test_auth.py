import pytest
import time
import transaction

from datetime import timedelta
from onegov.core import Framework
from onegov.core.security.identity_policy import IdentityPolicy
from onegov.core.utils import Bunch
from onegov.user import Auth, UserCollection, UserApp
from onegov.user.errors import ExpiredSignupLinkError
from sedate import utcnow
from unittest.mock import patch
from webtest import TestApp as Client
from yubico_client import Yubico


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


class DummyApp:

    can_deliver_sms = True

    def __init__(self, session, application_id='my-app'):
        self._session = session
        self.application_id = application_id
        self.sent_sms = []

    def session(self):
        return self._session

    def send_sms(self, number, content):
        self.sent_sms.append((number, content))


def test_auth_login(session):
    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    auth = Auth(DummyApp(session))

    assert not auth.authenticate(
        request=None, username='AzureDiamond', password='hunter1')
    assert not auth.authenticate(
        request=None, username='AzureDiamonb', password='hunter2')
    user = auth.authenticate(
        request=None, username='AzureDiamond', password='hunter2')

    identity = auth.as_identity(user)
    assert identity.userid == 'azurediamond'
    assert identity.role == 'irc-user'
    assert identity.application_id == 'my-app'


def test_auth_login_inactive(session):
    user = UserCollection(session).add(
        'AzureDiamond', 'hunter2', 'irc-user', active=False)

    auth = Auth(DummyApp(session))

    assert not auth.authenticate(
        request=None, username='AzureDiamond', password='hunter2')

    user.active = True
    transaction.commit()

    assert auth.authenticate(
        request=None, username='AzureDiamond', password='hunter2')


def test_auth_login_yubikey(session):
    UserCollection(session).add(
        username='admin@example.org',
        password='p@ssw0rd',
        role='admin',
        second_factor={
            'type': 'yubikey',
            'data': 'ccccccbcgujh'
        }
    )

    app = DummyApp(session)
    app.yubikey_client_id = 'abc'
    app.yubikey_secret_key = 'dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE='

    auth = Auth(app)

    assert not auth.authenticate(
        request=None, username='admin@example.org', password='p@ssw0rd')
    assert not auth.authenticate(
        request=None,
        username='admin@example.org',
        password='p@ssw0rd',
        second_factor='xxxxxxbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = False

        assert not auth.authenticate(
            request=None,
            username='admin@example.org',
            password='p@ssw0rd',
            second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = True

        user = auth.authenticate(
            request=None,
            username='admin@example.org',
            password='p@ssw0rd',
            second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )

    identity = auth.as_identity(user)
    assert identity.userid == 'admin@example.org'
    assert identity.role == 'admin'
    assert identity.application_id == 'my-app'


def test_auth_login_unnecessary_yubikey(session):
    UserCollection(session).add(
        username='admin@example.org',
        password='p@ssw0rd',
        role='admin'
    )

    auth = Auth(DummyApp(session))

    # simply ignore the second factor
    assert auth.authenticate(
        request=None,
        username='admin@example.org',
        password='p@ssw0rd',
        second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )


def test_auth_logging(capturelog, session):
    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    auth = Auth(DummyApp(session))

    # XXX do not change the following messages, as they are used that way in
    # fail2ban already and should remain exactly the same
    capturelog.handler.records.clear()
    auth.authenticate(
        request=None, username='AzureDiamond', password='hunter1')
    assert capturelog.records()[0].message \
        == "Failed login by unknown (AzureDiamond)"

    capturelog.handler.records.clear()
    auth.authenticate(
        request=None, username='AzureDiamond', password='hunter1',
        client='127.0.0.1')
    assert capturelog.records()[0].message \
        == "Failed login by 127.0.0.1 (AzureDiamond)"

    capturelog.handler.records.clear()
    auth.authenticate(
        request=None, username='AzureDiamond', password='hunter2',
        client='127.0.0.1')
    assert capturelog.records()[0].message \
        == "Successful login by 127.0.0.1 (AzureDiamond)"


def test_auth_integration(session, redis_url):

    class App(Framework, UserApp):
        pass

    @App.identity_policy()
    def get_identity_policy():
        return IdentityPolicy()

    @App.path(path='/auth', model=Auth)
    def get_auth():
        return Auth(DummyApp(session), to='https://abc.xyz/go')

    @App.view(model=Auth)
    def view_auth(self, request):
        return self.login_to(
            request.params.get('username'),
            request.params.get('password'),
            request
        ) or 'Error'

    @App.view(model=Auth, name='logout')
    def view_logout(self, request):
        return self.logout_to(request)

    App.commit()

    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    transaction.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(
        identity_secure=False,
        redis_url=redis_url
    )
    app.application_id = 'test/foo'

    client = Client(app)

    response = client.get('/auth?username=AzureDiamond&password=hunter1')
    assert response.text == 'Error'
    assert not UserCollection(session).by_username('AzureDiamond').sessions

    response = client.get('/auth?username=AzureDiamond&password=hunter2')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'
    assert response.headers['Set-Cookie'].startswith('session_id')
    session_id = app.unsign(response.request.cookies['session_id'])
    user = UserCollection(session).by_username('AzureDiamond')
    assert session_id in user.sessions

    response = client.get('/auth/logout')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'

    user = UserCollection(session).by_username('AzureDiamond')
    assert not user.sessions

    response = client.get('/auth?username=AzureDiamond&password=hunter2')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'
    assert response.headers['Set-Cookie'].startswith('session_id')
    new_session_id = app.unsign(response.request.cookies['session_id'])
    assert new_session_id != session_id
    user = UserCollection(session).by_username('AzureDiamond')
    assert new_session_id in user.sessions


def test_signup_token_data(session):
    auth = Auth(DummyApp(session, 'foo'), signup_token_secret='bar')
    assert auth.new_signup_token('admin')

    token = auth.new_signup_token('admin', max_age=1)
    data = auth.decode_signup_token(token)
    assert data['role'] == 'admin'
    assert data['max_uses'] == 1

    now = utcnow().replace(tzinfo=None)
    before = int((now - timedelta(seconds=1)).timestamp())
    after = int((now + timedelta(seconds=1)).timestamp())
    assert before <= data['expires'] <= after


def test_signup_max_uses(session):
    auth = Auth(DummyApp(session, 'foo'), signup_token_secret='bar')
    auth.signup_token = auth.new_signup_token('admin', max_age=10, max_uses=1)

    foo = auth.register(
        form=Bunch(
            username=Bunch(data='foo@example.org'),
            password=Bunch(data='correct horse'),
        ),
        request=Bunch(
            client_addr='127.0.0.1'
        )
    )

    assert foo.role == 'admin'

    with pytest.raises(ExpiredSignupLinkError):
        auth.register(
            form=Bunch(
                username=Bunch(data='bar@example.org'),
                password=Bunch(data='battery staple'),
            ),
            request=Bunch(
                client_addr='127.0.0.1'
            )
        )


def test_signup_expired(session):
    auth = Auth(DummyApp(session, 'foo'), signup_token_secret='bar')
    auth.signup_token = auth.new_signup_token('admin', max_age=1, max_uses=2)

    foo = auth.register(
        form=Bunch(
            username=Bunch(data='foo@example.org'),
            password=Bunch(data='correct horse'),
        ),
        request=Bunch(
            client_addr='127.0.0.1'
        )
    )

    assert foo.role == 'admin'

    time.sleep(2)

    with pytest.raises(ExpiredSignupLinkError):
        auth.register(
            form=Bunch(
                username=Bunch(data='bar@example.org'),
                password=Bunch(data='battery staple'),
            ),
            request=Bunch(
                client_addr='127.0.0.1'
            )
        )
