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
    app.configure_application(
        dsn=postgres_dsn,
        redis_url=redis_url,
    )

    return app


def configure_provider(app, app_id, metadata):
    config = textwrap.dedent(f"""
        authentication_providers:
          saml2:
            tenants:
              "{app_id}":
                  metadata: "{metadata}"
                  button_text: Login with SAML2
            roles:
              "{app_id}":
                admins: 'ads'
                editors: 'eds'
                members: 'mems'
        """)

    app.configure_authentication_providers(**yaml.safe_load(config))


def test_saml2_configuration(app, idp_metadata):

    namespace = 'saml2'
    app_id = f'{namespace}/test'
    app.namespace = namespace
    app.set_application_id(app_id)
    configure_provider(app, app_id, idp_metadata)

    provider = app.providers[0]
    client = provider.tenants.client(app)

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'uid'
    assert client.attributes.username == 'email'
    assert client.attributes.groups == 'member'
    assert client.attributes.first_name == 'givenName'
    assert client.attributes.last_name == 'sn'

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }


def test_saml2_authenticate_request(app, idp_metadata):

    namespace = 'saml2'
    app_id = f'{namespace}/test'
    app.namespace = namespace
    app.set_application_id(app_id)
    configure_provider(app, app_id, idp_metadata)

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
