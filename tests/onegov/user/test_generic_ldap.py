from __future__ import annotations

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


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest
    from pathlib import Path


class App(Framework, UserApp):
    pass


@pytest.fixture(scope='function')
def app(
    request: pytest.FixtureRequest,
    glauth_binary: str,
    postgres_dsn: str,
    temporary_path: Path,
    redis_url: str,
    keytab: str
) -> Iterator[App]:

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

    class _App(App):
        pass

    @_App.path(path='/private')
    class PrivateDocument:
        name = 'private'

    @_App.path(path='/secret')
    class SecretDocument:
        name = 'secret'

    @_App.path(path='/auth', model=Auth)
    def get_auth(request: CoreRequest, app: App) -> Auth:
        return Auth(app)

    @_App.view(model=Auth, permission=Public, name='login')
    def view_auth(self: Auth, request: CoreRequest) -> str:
        return 'login-page'

    @_App.view(model=Auth, permission=Public, name='login',
              request_method='POST')
    def handle_auth(self: Auth, request: CoreRequest) -> str:
        if self.login_to(
                request.params['username'],  # type: ignore[arg-type]
                request.params['password'],  # type: ignore[arg-type]
                request):

            return 'success'

        return 'unauthorized'

    @_App.json(model=PrivateDocument, permission=Private)
    def view_private(
        self: PrivateDocument,
        request: CoreRequest
    ) -> object:
        return {
            'name': self.name,
            'user': request.identity.userid
        }

    @_App.json(model=SecretDocument, permission=Secret)
    def view_secret(self: SecretDocument, request: CoreRequest) -> object:
        return {
            'name': self.name,
            'user': request.identity.userid
        }

    scan_morepath_modules(_App)
    morepath.commit(_App)

    with GLAuth(glauth_binary, config) as ldap_server:
        ldap_host = ldap_server.context.host
        ldap_port = ldap_server.context.port

        app = _App()
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
def client(app: App) -> Iterator[Client]:
    yield Client(app)


def test_generic_ldap(
    client: Client,
    app: App,
    caplog: pytest.LogCaptureFixture
) -> None:

    assert 'login-page' in client.get('/auth/login')
    assert client.get('/private', status=403)
    assert client.get('/secret', status=403)

    app.providers['ldap'].ldap.compare = MagicMock()  # type: ignore[union-attr]

    app.providers['ldap'].ldap.compare.return_value = False  # type: ignore[union-attr]
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'editor@seantis.ch',
        'password': 'hunter2'
    })

    app.providers['ldap'].ldap.compare.return_value = True  # type: ignore[union-attr]
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
    app.providers['ldap'].ldap.compare.return_value = False  # type: ignore[union-attr]
    assert 'unauthorized' in client.post('/auth/login', {
        'username': 'editor',
        'password': 'wrong'
    })
    assert 'Wrong password for editor@seantis.ch' in caplog.text

    # wrong role
    app.providers['ldap'].ldap.compare.return_value = True  # type: ignore[union-attr]
    app.providers['ldap'].ldap.search = MagicMock()  # type: ignore[union-attr]
    app.providers['ldap'].ldap.search.return_value = {  # type: ignore[union-attr]
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
    app.providers['ldap'].ldap.search.return_value = {  # type: ignore[union-attr]
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
    app.providers['ldap'].ldap.search.side_effect = [  # type: ignore[union-attr]
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
