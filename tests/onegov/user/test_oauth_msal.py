import os
import textwrap

import morepath
import pytest
import yaml

from onegov.core import Framework
from onegov.core.utils import scan_morepath_modules
from onegov.user import UserApp

# App url set in our AzureAD test tenant
MSAL_TEST_FQGN = os.environ.get('MSAL_TEST_FQGN')

# We only hardcode our tenant here for the devs convenience to not set it
# with env vars, since it is needed due to the tenant check in msal,
# however the rest should be kept secret
TEST_TENANT = os.environ.get(
    'MSAL_TEST_TENANT', 'c6d19353-f861-49e7-bf0b-d5eff6b2624c'
)


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


def configure_provider(app, app_id):
    client_id = os.environ.get('MSAL_TEST_CLIENT_ID')
    client_secret = os.environ.get('MSAL_TEST_CLIENT_SECRET')
    config = textwrap.dedent(f"""
        authentication_providers:
          msal:
            tenants:
              "{app_id}":
                tenant_id: '{TEST_TENANT}'
                client_id: '{client_id}'
                client_secret: '{client_secret}'
                validate_authority: false
                #attributes:
                #  source_id: 'sub'
                #  username: 'email'
                #  groups: 'groups'
                #  first_name: 'given_name'
                #  last_name: 'family_name'
            roles:
              "{app_id}":
                admins: 'ads'
                editors: 'eds'
                members: 'mems'
        """)

    app.configure_authentication_providers(**yaml.safe_load(config))


def test_msal_configuration(app):

    namespace = 'msal'
    app_id = f'{namespace}/test'
    app.namespace = namespace
    app.set_application_id(app_id)
    configure_provider(app, app_id)

    provider = app.providers[0]
    client = provider.tenants.client(app)
    assert not client.validate_authority

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'sub'
    assert client.attributes.username == 'email'
    assert client.attributes.groups == 'groups'
    assert client.attributes.first_name == 'given_name'
    assert client.attributes.last_name == 'family_name'
    assert client.attributes.preferred_username == 'preferred_username'

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }


@pytest.mark.skipif(MSAL_TEST_FQGN, reason='Running in CI/CD')
def test_msal_client_local(app):
    pass


@pytest.mark.skipif(not MSAL_TEST_FQGN, reason='Running locally')
def test_msal_client_ci(app):
    pass
