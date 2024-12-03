import json
import textwrap

import morepath
import pytest
import yaml

from onegov.core import Framework
from onegov.core.utils import scan_morepath_modules, Bunch
from onegov.user import UserApp


@pytest.fixture(scope='function')
def app(postgres_dsn, redis_url):

    class App(Framework, UserApp):
        pass

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'oidc'
    app.configure_application(
        dsn=postgres_dsn,
        redis_url=redis_url,
    )
    app.set_application_id('oidc/test')

    return app


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    monkeypatch.delattr("requests.sessions.Session.request")


def configure_provider(app, metadata=None, primary=False):
    config = textwrap.dedent(f"""
        authentication_providers:
          idp:
            provider: oidc
            tenants:
              "{app.application_id}":
                primary: {'true' if primary else 'false'}
                issuer: https://oidc.test/
                client_id: test
                client_secret: secret
                button_text: Login with OIDC
                fixed_metadata: {json.dumps(metadata or {})}
            roles:
              "{app.application_id}":
                admins: 'ads'
                editors: 'eds'
                members: 'mems'
        """)

    app.configure_authentication_providers(**yaml.safe_load(config))


def test_oidc_configuration(app):
    configure_provider(app)

    provider = app.providers['idp']
    client = provider.tenants.client(app)

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'sub'
    assert client.attributes.username == 'email'
    assert client.attributes.group == 'group'
    assert client.attributes.first_name == 'given_name'
    assert client.attributes.last_name == 'family_name'
    assert client.attributes.preferred_username == 'preferred_username'
    assert client.primary is False

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }
    assert provider.is_primary(app) is False


def test_oidc_configuration_primary(app):
    configure_provider(app, primary=True)

    provider = app.providers['idp']
    client = provider.tenants.client(app)

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'sub'
    assert client.attributes.username == 'email'
    assert client.attributes.group == 'group'
    assert client.attributes.first_name == 'given_name'
    assert client.attributes.last_name == 'family_name'
    assert client.attributes.preferred_username == 'preferred_username'
    assert client.primary is True

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }
    assert provider.is_primary(app) is True


def test_oidc_static_metadata(app):
    static_metadata = {
        'issuer': 'https://oidc.test/',
        'authorization_endpoint': 'https://oidc.test/authorize',
        'jwks_uri': 'https://oidc.test/jwks',
        'response_types_supported': [
            'code'
        ],
        'response_modes_supported': [
            'query',
            'form_post'
        ],
        'grant_types_supported': [
            'authorization_code',
            'refresh_token'
        ],
        'code_challenge_methods_supported': [
            'plain',
            'S256'
        ],
    }
    configure_provider(app, static_metadata)

    provider = app.providers['idp']
    client = provider.tenants.client(app)
    metadata = client.metadata(Bunch(app=app))
    # not technically part of the metadata...
    metadata.pop('jwks_client')
    assert static_metadata == metadata


def test_oicd_authenticate_request(app):

    configure_provider(app, {
        'issuer': 'https://oidc.test/',
        'authorization_endpoint': 'https://oidc.test/authorize',
        'jwks_uri': 'https://oidc.test/jwks',
        'response_types_supported': [
            'code'
        ],
        'response_modes_supported': [
            'query',
            'form_post'
        ],
        'grant_types_supported': [
            'authorization_code',
            'refresh_token'
        ],
        'code_challenge_methods_supported': [
            'plain',
            'S256'
        ],
    })

    provider = app.providers['idp']
    provider.to = '/'

    # test authenticate request
    browser_session = {}
    request = Bunch(
        app=app,
        application_url='http://example.com/',
        url='http://example.com/auth/provider/idp',
        browser_session=browser_session,
        class_link=lambda cls, args, name:
        f'http://example.com/auth/provider/{args["name"]}/{name}',
        csrf_salt='salt',
        new_url_safe_token=lambda data, salt: 'oauth_state')
    response = provider.authenticate_request(request)
    assert response.status_code == 302
    location = response.headers['Location']
    assert location.startswith('https://oidc.test/authorize')
    assert 'state=oauth_state' in location
    assert 'scope=openid' in location
    assert browser_session['login_to'] == '/'


def test_oidc_client(app):
    pass
