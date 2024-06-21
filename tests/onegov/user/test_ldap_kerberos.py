
import kerberos
import morepath
import pytest

from hashlib import sha256
from onegov.core import Framework
from onegov.core.security import Public, Private, Secret
from onegov.core.utils import scan_morepath_modules, module_path
from onegov.user import Auth, UserApp
from tests.shared.glauth import GLAuth
from unittest.mock import patch, DEFAULT
from tests.shared.client import Client


@pytest.fixture(scope='function')
def app(request, glauth_binary, postgres_dsn, temporary_path, redis_url,
        keytab):

    config = f"""
        debug = true

        [ldap]
        enabled = false

        [ldaps]
        enabled = true
        listen = "%(host)s:%(port)s"
        cert = "{module_path('tests.shared', 'fixtures/self-signed.crt')}"
        key = "{module_path('tests.shared', 'fixtures/self-signed.key')}"

        [backend]
        datastore = "config"
        baseDN = "dc=seantis,dc=ch"

        # SERVICE ACCOUNTS
        [[groups]]
        name = "service"
        unixid = 5000

        [[users]]
        name = "service"
        unixid = 1000
        primarygroup = 5000
        passsha256 = "{sha256(b'hunter2').hexdigest()}"

        # ADMIN ACCOUNTS
        [[groups]]
        name = "admins"
        unixid = 5100

        [[users]]
        name = "admin"
        mail = "admin@seantis.ch"
        unixid = 1001
        primarygroup = 5100
        passsha256 = "{sha256(b'hunter2').hexdigest()}"

        # EDITOR ACCOUNTS
        [[groups]]
        name = "editors"
        unixid = 5200

        [[users]]
        name = "editor"
        mail = "editor@seantis.ch"
        unixid = 1001
        primarygroup = 5200
        passsha256 = "{sha256(b'hunter2').hexdigest()}"

    """

    class App(Framework, UserApp):
        pass

    @App.path(path='/private')
    class PrivateDocument:
        name = 'private'

    @App.path(path='/secret')
    class SecretDocument:
        name = 'secret'

    @App.path(path='/auth', model=Auth)
    def get_auth(request, app):
        return Auth(app)

    @App.view(model=Auth, permission=Public, name='login')
    def view_auth(self, request):
        return 'login-page'

    @App.json(model=PrivateDocument, permission=Private)
    def view_private(self, request):
        return {
            'name': self.name,
            'user': request.identity.userid
        }

    @App.json(model=SecretDocument, permission=Secret)
    def view_secret(self, request):
        return {
            'name': self.name,
            'user': request.identity.userid
        }

    scan_morepath_modules(App)
    morepath.commit(App)

    with GLAuth(glauth_binary, config) as ldap_server:
        ldap_host = ldap_server.context.host
        ldap_port = ldap_server.context.port

        app = App()
        app.namespace = 'apps'
        app.configure_application(
            dsn=postgres_dsn,
            redis_url=redis_url,
            identity_secure=False,
            authentication_providers={
                'ldap_kerberos': {
                    'ldap_url': f'ldaps://{ldap_host}:{ldap_port}',
                    'ldap_username': 'cn=service,ou=service,dc=seantis,dc=ch',
                    'ldap_password': 'hunter2',
                    'kerberos_keytab': keytab,
                    'kerberos_hostname': 'ogc.example.org',
                    'kerberos_service': 'HTTP',
                }
            }
        )

        app.set_application_id('apps/my-app')

        yield app


@pytest.fixture(scope='function')
def client(app):
    yield Client(app)


def test_ldap_kerberos_provider(client):

    def set_kerberos_user(methods, username):
        methods['authGSSServerInit'].return_value = 1, None
        methods['authGSSServerStep'].return_value = 1
        methods['authGSSServerResponse'].return_value = 'foobar'
        methods['authGSSServerUserName'].return_value = username

    def get(path):
        url = f'/auth/provider/ldap_kerberos?to={path}'
        headers = {'Authorization': 'Negotiate foobar'}

        page = client.spawn().get(url, headers=headers, expect_errors=True)
        return page.maybe_follow(expect_errors=True)

    # for our tests we must mock the answers, setting up
    # a Kerberos environment is no easy task
    methods = {
        'authGSSServerInit': DEFAULT,
        'authGSSServerStep': DEFAULT,
        'authGSSServerResponse': DEFAULT,
        'authGSSServerUserName': DEFAULT,
    }
    with patch.multiple(kerberos, **methods) as methods:

        set_kerberos_user(methods, 'admin')
        assert get('/private').json == {
            'name': 'private',
            'user': 'admin@seantis.ch'
        }

        assert get('/secret').json == {
            'name': 'secret',
            'user': 'admin@seantis.ch'
        }

        set_kerberos_user(methods, 'editor')
        assert get('/private').json == {
            'name': 'private',
            'user': 'editor@seantis.ch'
        }

        assert get('/secret').status_code == 403

        set_kerberos_user(methods, 'anonymous')
        assert 'login-page' in get('/private')
        assert 'login-page' in get('/secret')
