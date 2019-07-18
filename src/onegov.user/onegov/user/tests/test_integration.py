import base64
import kerberos
import morepath
import pytest
import transaction

from onegov.core import Framework
from onegov.core.utils import scan_morepath_modules
from onegov.user import Auth, UserApp, UserCollection
from onegov.user.auth.provider import provider_by_name
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

    # Auth needs to be linkable
    @App.path(model=Auth, path='/auth')
    def get_auth(request):
        return None

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.configure_application(
        dsn=postgres_dsn,
        redis_url=redis_url,
        authentication_providers={
            'kerberos': {
                'keytab': keytab,
                'hostname': 'ogc.example.org',
                'service': 'HTTP'
            }
        }
    )

    app.namespace = 'apps'
    app.set_application_id('apps/my-app')

    return app


@pytest.fixture(scope='function')
def client(app):
    yield Client(app)


def test_kerberos_auth(client, app):
    provider = provider_by_name(app.providers, 'kerberos')
    assert provider is not None

    def auth(headers=None):
        return client.get(
            url='/auth/provider/kerberos',
            expect_errors=True,
            headers=headers
        )

    # initially, the answer is 401 Unauthorized, to which Kerberos clients
    # are meant to answer with a ticket/token
    r = auth()
    assert r.status_code == 401
    assert r.headers['WWW-Authenticate'] == 'Negotiate'

    # for our tests we fake must mock the answers somewhat, setting up
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

        # simulate a successful exchange, with no associated user
        methods['authGSSServerInit'].return_value = 1, None
        methods['authGSSServerStep'].return_value = 1
        methods['authGSSServerResponse'].return_value = 'barfoo'
        methods['authGSSServerUserName'].return_value = 'foo@EXAMPLE.ORG'
        r = auth({'Authorization': 'Negotiate foobar'})

        assert r.status_code == 302
        assert r.location.endswith('/auth/login')

        # associate a user, but keep it inactive
        user = UserCollection(app.session()).add(
            username='foo@bar.org',
            password='foobar',
            role='member',
            active=False,
            authentication_provider={
                'name': 'kerberos',
                'fields': {
                    'username': 'foo@EXAMPLE.ORG'
                },
                'required': True
            }
        )
        transaction.commit()

        r = auth({'Authorization': 'Negotiate foobar'})
        assert r.status_code == 302
        assert r.location.endswith('/auth/login')

        # now activate the user
        user = UserCollection(app.session()).by_username('foo@bar.org')
        user.active = True
        transaction.commit()

        r = auth({'Authorization': 'Negotiate foobar'})
        assert r.status_code == 302
        assert r.location == 'http://localhost/'
        assert r.headers['Set-Cookie'].startswith('session_id')

        # since the user *requires* the auth provider, a normal login
        # is no longer possible
        auth = Auth.from_app(app)
        assert not auth.authenticate('foo@bar.org', password='foobar')

        # unless we make it optional
        user = UserCollection(app.session()).by_username('foo@bar.org')
        user.authentication_provider['required'] = False
        transaction.commit()

        auth = Auth.from_app(app)
        assert auth.authenticate('foo@bar.org', password='foobar')
