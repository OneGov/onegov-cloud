from __future__ import annotations

import msal  # type:ignore[import-untyped]
from attr import attrs, attrib
from functools import cached_property

from onegov.user import log


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.user.auth.provider import HasApplicationIdAndNamespace
    from typing import Self


@attrs(auto_attribs=True)
class AzureADAttributes:
    """ Holds the expected AzureAD id_token_claims used to ensure the user """

    # the unique id in Azure per Application if sub is used
    # or globally in AzureAd if oid is used.
    source_id: str

    # name for the username in User, can also be `preferred_username`
    username: str

    # The users first name if available, use for User.realname
    first_name: str

    # The users last name if available, use for User.realname
    last_name: str

    # the name of the groups per tenant id, groups roles or scp
    groups: str

    # A field from Azure designating a display name, can be anything
    # Can be used if first / last name are not available to fill User.realname
    preferred_username: str

    @classmethod
    def from_cfg(cls, cfg: dict[str, Any]) -> Self:
        return cls(
            source_id=cfg.get('source_id', 'sub'),
            username=cfg.get('username', 'email'),
            groups=cfg.get('groups', 'groups'),
            first_name=cfg.get('first_name', 'given_name'),
            last_name=cfg.get('last_name', 'family_name'),
            preferred_username='preferred_username'
        )


@attrs()
class MSALClient:

    AUTHORITY_BASE = 'https://login.microsoftonline.com'
    SIGN_OUT_ENDPOINT = '/oauth2/v2.0/logout'

    client_id: str = attrib()

    client_secret: str = attrib()

    tenant_id: str = attrib()

    # this is useful for testing
    validate_authority: bool = attrib()

    # Needed attributes in id_token_claim
    attributes: AzureADAttributes = attrib()

    primary: bool = attrib()

    @cached_property
    def connection(self) -> msal.ConfidentialClientApplication:
        """ Returns the msal instance. Upon initiation, the client tries to
        connect to the authority endpoint. msal always validate the the tenant
        with an tenant discovery, `validate_authority` will additionally check
        the host/instance.
        """
        try:
            client = msal.ConfidentialClientApplication(
                self.client_id,
                authority=self.authority,     # is tenant specific!
                client_credential=self.client_secret,
                token_cache=None,
                validate_authority=self.validate_authority
            )
        except Exception as exception:
            raise ValueError(
                f'MSAL config error in tenant {self.tenant_id}: '
                '{str(exception)}'
            ) from exception
        return client

    @property
    def authority(self) -> str:
        return f'{self.AUTHORITY_BASE}/{self.tenant_id}'

    def logout_url(self, logout_redirect: str) -> str:
        url_param = f'?post_logout_redirect_uri={logout_redirect}'
        return f'{self.authority}{self.SIGN_OUT_ENDPOINT}{url_param}'


@attrs
class MSALConnections:

    # instantiated connections for every tenant
    connections: dict[str, MSALClient] = attrib()

    def client(self, app: HasApplicationIdAndNamespace) -> MSALClient | None:
        if app.application_id in self.connections:
            return self.connections[app.application_id]

        if app.namespace in self.connections:
            return self.connections[app.namespace]
        return None

    @classmethod
    def from_cfg(cls, config: dict[str, Any]) -> Self:
        clients = {
            app_id: MSALClient(
                client_id=cfg['client_id'],
                client_secret=cfg['client_secret'],
                tenant_id=cfg['tenant_id'],
                validate_authority=cfg.get('validate_authority', True),
                attributes=AzureADAttributes.from_cfg(
                    cfg.get('attributes', {})
                ),
                primary=cfg.get('primary', False),
            ) for app_id, cfg in config.items()
        }
        for app_id, client in clients.items():
            # instantiate and cache the connection on app startup
            success = client.connection
            if success and client.validate_authority:
                log.info(f'MSAL connection successfull: {app_id}')

        return cls(connections=clients)
