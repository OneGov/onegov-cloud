import morepath
import transaction

from more.itsdangerous import IdentityPolicy
from onegov.user import (
    Auth, is_valid_yubikey, is_valid_yubikey_format,
    UserCollection, yubikey_otp_to_serial
)
from webtest import TestApp as Client
from unittest.mock import patch
from yubico_client import Yubico


def test_auth_login(session):
    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    auth = Auth(session=session, application_id='my-app')

    assert not auth.login(username='AzureDiamond', password='hunter1')
    assert not auth.login(username='AzureDiamonb', password='hunter2')

    identity = auth.login(username='AzureDiamond', password='hunter2')
    assert identity.userid == 'AzureDiamond'
    assert identity.role == 'irc-user'
    assert identity.application_id == 'my-app'


def test_auth_login_inactive(session):
    user = UserCollection(session).add(
        'AzureDiamond', 'hunter2', 'irc-user', active=False)

    auth = Auth(session=session, application_id='my-app')

    assert not auth.login(username='AzureDiamond', password='hunter2')

    user.active = True
    transaction.commit()

    assert auth.login(username='AzureDiamond', password='hunter2')


def test_is_valid_yubikey_otp(session):

    assert not is_valid_yubikey(
        client_id='abc',
        secret_key='dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE=',
        expected_yubikey_id='ccccccbcgujx',
        yubikey='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = True

        assert is_valid_yubikey(
            client_id='abc',
            secret_key='dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE=',
            expected_yubikey_id='ccccccbcgujh',
            yubikey='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )


def test_is_valid_yubikey_format():
    assert is_valid_yubikey_format('ccccccdefghd')
    assert is_valid_yubikey_format('cccccccdefg' * 4)
    assert not is_valid_yubikey_format('ccccccdefghx')


def test_yubikey_otp_to_serial():
    assert yubikey_otp_to_serial(
        'ccccccdefghdefghdefghdefghdefghdefghdefghklv') == 2311522
    assert yubikey_otp_to_serial("ceci n'est pas une yubikey") is None


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

    auth = Auth(
        session=session,
        application_id='my-app',
        yubikey_client_id='abc',
        yubikey_secret_key='dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE='
    )

    assert not auth.login(username='admin@example.org', password='p@ssw0rd')
    assert not auth.login(
        username='admin@example.org',
        password='p@ssw0rd',
        second_factor='xxxxxxbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = False

        assert not auth.login(
            username='admin@example.org',
            password='p@ssw0rd',
            second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = True

        identity = auth.login(
            username='admin@example.org',
            password='p@ssw0rd',
            second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )

    assert identity.userid == 'admin@example.org'
    assert identity.role == 'admin'
    assert identity.application_id == 'my-app'


def test_auth_login_unnecessary_yubikey(session):
    UserCollection(session).add(
        username='admin@example.org',
        password='p@ssw0rd',
        role='admin'
    )

    auth = Auth(
        session=session,
        application_id='my-app',
    )

    # simply ignore the second factor
    assert auth.login(
        username='admin@example.org',
        password='p@ssw0rd',
        second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )


def test_auth_logging(session, capturelog):
    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    auth = Auth(session=session, application_id='my-app')

    auth.login(username='AzureDiamond', password='hunter1')
    assert capturelog.records()[0].message \
        == "Failed login by unknown (AzureDiamond)"

    auth.login(username='AzureDiamond', password='hunter1', client='127.0.0.1')
    assert capturelog.records()[1].message \
        == "Failed login by 127.0.0.1 (AzureDiamond)"

    auth.login(username='AzureDiamond', password='hunter2', client='127.0.0.1')
    assert capturelog.records()[2].message \
        == "Successful login by 127.0.0.1 (AzureDiamond)"


def test_auth_integration(session):

    class App(morepath.App):
        pass

    @App.identity_policy()
    def get_identity_policy():
        return IdentityPolicy()

    @App.path(path='/auth', model=Auth)
    def get_auth():
        return Auth(session, application_id='my_app', to='https://abc.xyz/go')

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

    client = Client(App())

    response = client.get('/auth?username=AzureDiamond&password=hunter1')
    assert response.text == 'Error'

    response = client.get('/auth?username=AzureDiamond&password=hunter2')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'
    assert response.headers['Set-Cookie'].startswith('userid=AzureDiamond')

    response = client.get('/auth/logout')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'
    assert response.headers['Set-Cookie'].startswith('userid=;')
