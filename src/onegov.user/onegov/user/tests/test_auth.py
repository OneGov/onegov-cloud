import morepath
import transaction

from more.itsdangerous import IdentityPolicy
from onegov.user import Auth, UserCollection
from webtest import TestApp as Client


def test_auth_login(session):
    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    auth = Auth(session=session, application_id='my-app')

    assert not auth.login(username='AzureDiamond', password='hunter1')
    assert not auth.login(username='AzureDiamonb', password='hunter2')

    identity = auth.login(username='AzureDiamond', password='hunter2')
    assert identity.userid == 'AzureDiamond'
    assert identity.role == 'irc-user'
    assert identity.application_id == 'my-app'


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

    config = morepath.setup()

    class App(morepath.App):
        testing_config = config

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

    config.commit()

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
