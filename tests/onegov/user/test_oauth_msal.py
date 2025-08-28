from __future__ import annotations

import os
import textwrap

import morepath
import pytest
import yaml

from onegov.core import Framework
from onegov.core.utils import scan_morepath_modules
from onegov.user import UserApp
from onegov.user.auth.provider import AzureADProvider

# App url set in our AzureAD test tenant
MSAL_TEST_FQGN = os.environ.get('MSAL_TEST_FQGN', '')

# We only hardcode our tenant here for the devs convenience to not set it
# with env vars, since it is needed due to the tenant check in msal,
# however the rest should be kept secret
TEST_TENANT = os.environ.get(
    'MSAL_TEST_TENANT', 'c6d19353-f861-49e7-bf0b-d5eff6b2624c'
)


class App(Framework, UserApp):
    pass


@pytest.fixture(scope='function')
def app(postgres_dsn: str, redis_url: str) -> App:

    scan_morepath_modules(App)
    morepath.commit(App)

    app = App()
    app.namespace = 'msal'
    app.configure_application(
        dsn=postgres_dsn,
        redis_url=redis_url,
    )
    app.set_application_id('msal/test')

    return app


def configure_provider(app: App, primary: bool = False) -> None:
    client_id = os.environ.get('MSAL_TEST_CLIENT_ID')
    client_secret = os.environ.get('MSAL_TEST_CLIENT_SECRET')
    config = textwrap.dedent(f"""
        authentication_providers:
          msal:
            tenants:
              "{app.application_id}":
                primary: {'true' if primary else 'false'}
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
              "{app.application_id}":
                admins: 'ads'
                editors: 'eds'
                members: 'mems'
        """)

    app.configure_authentication_providers(**yaml.safe_load(config))


def test_msal_configuration(app: App) -> None:
    configure_provider(app)

    provider = app.providers['msal']
    assert isinstance(provider, AzureADProvider)
    client = provider.tenants.client(app)
    assert client is not None
    assert not client.validate_authority

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'sub'
    assert client.attributes.username == 'email'
    assert client.attributes.groups == 'groups'
    assert client.attributes.first_name == 'given_name'
    assert client.attributes.last_name == 'family_name'
    assert client.attributes.preferred_username == 'preferred_username'
    assert client.primary is False

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }
    assert provider.is_primary(app) is False


def test_msal_configuration_primary(app: App) -> None:
    configure_provider(app, primary=True)

    provider = app.providers['msal']
    assert isinstance(provider, AzureADProvider)
    client = provider.tenants.client(app)
    assert client is not None
    assert not client.validate_authority

    # Test default configuration of the commented blocks
    assert client.attributes.source_id == 'sub'
    assert client.attributes.username == 'email'
    assert client.attributes.groups == 'groups'
    assert client.attributes.first_name == 'given_name'
    assert client.attributes.last_name == 'family_name'
    assert client.attributes.preferred_username == 'preferred_username'
    assert client.primary is True

    assert provider.roles.app_specific(app) == {
        'admins': 'ads', 'editors': 'eds', 'members': 'mems'
    }
    assert provider.is_primary(app) is True


@pytest.mark.skipif(MSAL_TEST_FQGN, reason='Running in CI/CD')
def test_msal_client_local(app: App) -> None:
    pass


@pytest.mark.skipif(not MSAL_TEST_FQGN, reason='Running locally')
def test_msal_client_ci(app: App) -> None:
    pass
