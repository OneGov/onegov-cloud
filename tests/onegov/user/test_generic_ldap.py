import morepath
import pytest

from hashlib import sha256
from onegov.core import Framework
from onegov.core.security import Public, Private, Secret
from onegov.core.utils import scan_morepath_modules, module_path
from onegov.user import Auth, UserApp
from tests.shared.glauth import GLAuth
from tests.shared.client import Client
from unittest.mock import MagicMock


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
        unixid = 1002
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

    @App.view(model=Auth, permission=Public, name='login',
              request_method='POST')
    def handle_auth(self, request):
        if self.login_to(
                request.params.get('username'),
                request.params.get('password'),
                request):

            return 'success'

        return 'unauthorized'

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
                'ldap': {
                    'ldap_url': f'ldaps://{ldap_host}:{ldap_port}',
                    'ldap_username': 'cn=service,ou=service,dc=seantis,dc=ch',
                    'ldap_password': 'hunter2',
                    'roles': {
                        '__default__': {
                            'admins': 'cn=admins,ou=groups,dc=seantis,dc=ch',
                            'editors': 'cn=editors,ou=groups,dc=seantis,dc=ch',
                            'members': 'cn=members,ou=groups,dc=seantis,dc=ch',
                        }
                    }
                }
            }
        )

        app.set_application_id('apps/my-app')

        yield app


@pytest.fixture(scope='function')
def client(app):
    yield Client(app)


def test_generic_ldap(client, caplog):

    assert 'login-page' in client.get('/auth/login')
    assert client.get('/private', status=403)
    assert client.get('/secret', status=403)

    client.app.providers['ldap'].ldap.compare = MagicMock()

    client.app.providers['ldap'].ldap.compare.return_value = False
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'editor@seantis.ch',
        'password': 'hunter2'
    })

    client.app.providers['ldap'].ldap.compare.return_value = True
    assert 'success' in client.post('/auth/login', {
        'username': 'editor@seantis.ch',
        'password': 'hunter2'
    })

    assert client.get('/private', status=200)
    assert client.get('/secret', status=403)

    assert 'success' in client.post('/auth/login', {
        'username': 'admin@seantis.ch',
        'password': 'hunter2'
    })

    assert client.get('/private', status=200)
    assert client.get('/secret', status=200)

    # the uid can be used alternatively
    assert 'success' in client.post('/auth/login', {
        'username': 'admin',
        'password': 'hunter2'
    })

    assert 'success' in client.post('/auth/login', {
        'username': 'editor',
        'password': 'hunter2'
    })

    # no ldap user
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'tester',
        'password': 'hunter2'
    })
    assert 'No LDAP user with uid ore-mail tester' in caplog.text

    # wrong password
    client.app.providers['ldap'].ldap.compare.return_value = False
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'editor',
        'password': 'wrong'
    })
    assert 'Wrong password for editor@seantis.ch' in caplog.text

    # wrong role
    client.app.providers['ldap'].ldap.compare.return_value = True
    client.app.providers['ldap'].ldap.search = MagicMock()
    client.app.providers['ldap'].ldap.search.return_value = {
        'cn=editors,ou=groups,dc=seantis,dc=ch': {
            'memberOf': ['cn=unknown_group,ou=groups,dc=seantis,dc=ch'],
            'mail': ['user@example.com'],
            'uid': ['user']
        }
    }
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'onegov',
        'password': 'hunter2'
    })
    assert 'Wrong role for onegov' in caplog.text

    # multiple ldap entries
    client.app.providers['ldap'].ldap.search.return_value = {
        'cn=editors1,ou=groups,dc=seantis,dc=ch': {
            'memberOf': ['cn=group1,ou=groups,dc=seantis,dc=ch'],
            'mail': ['user@example.com'],
            'uid': ['user1']
        },
        'cn=editors2,ou=groups,dc=seantis,dc=ch': {
            'memberOf': ['cn=group2,ou=groups,dc=seantis,dc=ch'],
            'mail': ['user@example.com'],
            'uid': ['user2']
        }
    }
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'editor',
        'password': 'hunter2'
    })
    assert ('Found more than one user for e-mail editor' in
            caplog.text)
    assert 'All but the first user will be ignored' in caplog.text

    # LDAP search with missing email attribute
    client.app.providers['ldap'].ldap.search.side_effect = [
        {},
        {
            'cn=editors,ou=groups,dc=seantis,dc=ch': {
                'memberOf': ['cn=editors,ou=groups,dc=seantis,dc=ch'],
                'mail': [],
                'uid': ['user'],
            }
        },
        {
            'cn=editors,ou=groups,dc=seantis,dc=ch': {
                'memberOf': ['cn=editors,ou=groups,dc=seantis,dc=ch'],
                'mail': [],
                'uid': ['user'],
            }
        },
    ]
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'editor',
        'password': 'hunter2'
    })
    assert 'Email missing in LDAP for user with uid editor' in caplog.text
