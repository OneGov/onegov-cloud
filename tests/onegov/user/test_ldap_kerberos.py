from __future__ import annotations

import kerberos  # type: ignore[import-not-found]
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


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.core.request import CoreRequest
    from pathlib import Path
    from tests.shared.client import ExtendedResponse
    from unittest.mock import Mock


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
        unixid = 1001
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

    @_App.json(model=PrivateDocument, permission=Private)
    def view_private(self: PrivateDocument, request: CoreRequest) -> object:
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
def client(app: App) -> Iterator[Client]:
    yield Client(app)


def test_ldap_kerberos_provider(client: Client) -> None:

    def set_kerberos_user(methods: dict[str, Mock], username: str) -> None:
        methods['authGSSServerInit'].return_value = 1, None
        methods['authGSSServerStep'].return_value = 1
        methods['authGSSServerResponse'].return_value = 'foobar'
        methods['authGSSServerUserName'].return_value = username

    def get(path: str) -> ExtendedResponse:
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
