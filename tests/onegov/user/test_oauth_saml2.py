import os
import textwrap

import morepath
import pytest
import yaml

from onegov.core import Framework
from onegov.core.utils import Bunch, scan_morepath_modules
from onegov.user import UserApp

# location of our local SAML2 IdP metadata XML
IDP_METADATA = os.environ.get('SAML2_TEST_IDP_METADATA')


@pytest.fixture(scope='function')
def app(postgres_dsn, redis_url):

    class App(Framework, UserApp):
        pass

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'saml2'
    app.configure_application(
        dsn=postgres_dsn,
        redis_url=redis_url,
    )
    app.set_application_id('saml2/test')

    return app


def configure_provider(app, metadata, primary=False):
    config = textwrap.dedent(f"""
        authentication_providers:
          saml2:
            tenants:
              "{app.application_id}":
                primary: {'true' if primary else 'false'}
                metadata: "{metadata}"
                button_text: Login with SAML2
            roles:
              "{app.application_id}":
                admins: 'ads'
                editors: 'eds'
                members: 'mems'
        """)

    app.configure_authentication_providers(**yaml.safe_load(config))


def test_saml2_configuration(app, idp_metadata):

    configure_provider(app, idp_metadata)

    provider = app.providers[0]
    client = provider.tenants.client(app)

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'uid'
    assert client.attributes.username == 'email'
    assert client.attributes.groups == 'member'
    assert client.attributes.first_name == 'givenName'
    assert client.attributes.last_name == 'sn'
    assert client.primary is False

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }
    assert provider.is_primary(app) is False


def test_saml2_configuration_multiple_providers(app, idp_metadata):
    config = textwrap.dedent(f"""
        authentication_providers:
          idp_shpol:
            provider: saml2
            tenants:
              "{app.application_id}":
                primary: false
                metadata: "{idp_metadata}"
                button_text: Login with SHPOL
            roles:
              "{app.application_id}":
                admins: 'ads'
                editors: 'eds'
                members: 'mems'
          idp_sh:
            provider: saml2
            tenants:
              "{app.application_id}":
                primary: false
                metadata: "{idp_metadata}"
                button_text: Login with SH
            roles:
              "{app.application_id}":
                admins: 'ads'
                editors: 'eds'
                members: 'mems'
        """)

    app.configure_authentication_providers(**yaml.safe_load(config))

    assert len(app.providers) == 2

    provider1 = app.providers[0]
    assert provider1.metadata.name == 'saml2'
    client1 = provider1.tenants.client(app)
    assert client1.button_text == 'Login with SHPOL'

    provider2 = app.providers[1]
    assert provider2.metadata.name == 'saml2'
    client2 = provider2.tenants.client(app)
    assert client2.button_text == 'Login with SH'


def test_saml2_configuration_primary(app, idp_metadata):

    configure_provider(app, idp_metadata, primary=True)

    provider = app.providers[0]
    client = provider.tenants.client(app)

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'uid'
    assert client.attributes.username == 'email'
    assert client.attributes.groups == 'member'
    assert client.attributes.first_name == 'givenName'
    assert client.attributes.last_name == 'sn'
    assert client.primary is True

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }
    assert provider.is_primary(app) is True


def test_saml2_authenticate_request(app, idp_metadata):

    configure_provider(app, idp_metadata)

    provider = app.providers[0]
    provider.to = '/'

    # test authenticate request (requires xmlsec1 to be installed)
    request = Bunch(
        app=app,
        application_url='http://example.com/',
        url='http://example.com/auth/provider/saml2',
        class_link=lambda cls, args, name:
        f'http://example.com/auth/provider/{args["name"]}/{name}')
    response = provider.authenticate_request(request)
    assert response.status_code == 302
    location = response.headers['Location']
    assert location.startswith('https://testidp.zg.ch/login/sls/auth')
    assert 'SAMLRequest=' in location


@pytest.mark.skipif(IDP_METADATA, reason='Running in CI/CD')
def test_saml2_client_local(app, idp_metadata):
    pass


@pytest.mark.skipif(not IDP_METADATA, reason='Running locally')
def test_saml2_client_ci(app):
    pass
