import kerberos
import morepath
import pytest

from hashlib import sha256
from onegov.core import Framework
from onegov.core.security import Public
from onegov.core.utils import scan_morepath_modules, module_path
from onegov.user import UserApp
from onegov.user.auth.clients import KerberosClient, LDAPClient
from tests.shared.glauth import GLAuth
from unittest.mock import patch, DEFAULT
from webtest import TestApp as Client


@pytest.fixture(scope='function')
def app(request, postgres_dsn, temporary_path, redis_url, keytab):

    class App(Framework, UserApp):
        pass

    @App.path(model=KerberosClient, path='/kerberos-client')
    def get_kerberos_client(request):
        return KerberosClient(
            keytab=keytab,
            hostname='ogc.example.org',
            service='HTTP'
        )

    @App.view(model=KerberosClient, permission=Public)
    def view_kerberos_client(self, request):
        return self.authenticated_username(request)

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'apps'
    app.configure_application(
        dsn=postgres_dsn,
        redis_url=redis_url,
    )

    app.set_application_id('apps/my-app')

    return app


@pytest.fixture(scope='function')
def client(app):
    yield Client(app)


def test_kerberos_client(client, app, keytab):

    def auth(headers=None):
        return client.get(
            url='/kerberos-client',
            expect_errors=True,
            headers=headers
        )

    # initially, the answer is 401 Unauthorized, to which Kerberos clients
    # are meant to answer with a ticket/token
    r = auth()
    assert r.status_code == 401
    assert r.headers['WWW-Authenticate'] == 'Negotiate'

    # for our tests we must mock the answers, setting up
    # a Kerberos environment is no easy task
    methods = {
        'authGSSServerInit': DEFAULT,
        'authGSSServerStep': DEFAULT,
        'authGSSServerResponse': DEFAULT,
        'authGSSServerUserName': DEFAULT,
    }
    with patch.multiple(kerberos, **methods) as methods:
        assert methods

        # simulate a failing init step
        methods['authGSSServerInit'].return_value = -1, None
        r = auth({'Authorization': 'Negotiate foobar'})

        assert r.status_code == 401
        assert r.headers['WWW-Authenticate'] == 'Negotiate'

        # simulate a failing challenge step
        methods['authGSSServerInit'].return_value = 1, None
        methods['authGSSServerStep'].return_value = -1
        r = auth({'Authorization': 'Negotiate foobar'})

        assert r.status_code == 401
        assert r.headers['WWW-Authenticate'] == 'Negotiate'

        # simulate a successful exchange
        methods['authGSSServerInit'].return_value = 1, None
        methods['authGSSServerStep'].return_value = 1
        methods['authGSSServerResponse'].return_value = 'barfoo'
        methods['authGSSServerUserName'].return_value = 'foo@EXAMPLE.ORG'
        r = auth({'Authorization': 'Negotiate foobar'})

        assert r.text == 'foo@EXAMPLE.ORG'


def test_ldap_client(glauth_binary):
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

        [[groups]]
        name = "admins"
        unixid = 5000

        [[users]]
        name = "admin"
        mail = "admin@seantis.ch"
        unixid = 1000
        primarygroup = 5000
        passsha256 = "{sha256(b'hunter2').hexdigest()}"
    """

    with GLAuth(glauth_binary, config) as server:
        client = LDAPClient(
            url=f'ldaps://{server.context.host}:{server.context.port}',
            username='cn=admin,ou=admins,dc=seantis,dc=ch',
            password='hunter2')

        client.try_configuration()

        assert client.search('(objectClass=*)', attributes='mail') == {
            'cn=admin,ou=admins,dc=seantis,dc=ch': {
                'mail': ['admin@seantis.ch']
            }
        }
