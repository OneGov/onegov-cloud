import base64
import kerberos
import morepath
import pytest

from onegov.core import Framework
from onegov.core.security import Public
from onegov.core.utils import scan_morepath_modules
from onegov.user import UserApp
from onegov.user.auth.clients import KerberosClient
from tempfile import NamedTemporaryFile
from unittest.mock import patch, DEFAULT
from webtest import TestApp as Client


@pytest.fixture(scope='session')
def keytab():
    """ BASE 64 encoded keytab file for Kerberos integration tests

    Principal: HTTP/ogc.example.org@EXAMPLE.ORG
    Password: test

    To create, start ktutil (the latest release, macOS's one is too old):

        ktutil
        addent -password -p HTTP/ogc.example.org@EXAMPLE.ORG -k 1 -e aes256-cts
        wkt service.keytab
        exit
        cat service.keytab | base64

    """
    KEYTAB = (
        "BQIAAABXAAIAC0VYQU1QTEUuT1JHAARIVFRQAA9vZ2MuZXhhbXBsZS5vcmcAAAABXSxM"
        "KQEAEgAgKddJPBCQCDAtxV1NNksmnHT9xkbQLuO5rqFo+a6NEJMAAAAB"
    )

    with NamedTemporaryFile() as f:
        f.write(base64.b64decode(KEYTAB))
        f.flush()

        yield f.name


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
    app.configure_application(
        dsn=postgres_dsn,
        redis_url=redis_url,
    )

    app.namespace = 'apps'
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
