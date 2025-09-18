from __future__ import annotations

import requests
from attr import attrs, attrib
from base64 import urlsafe_b64encode
from jwt import PyJWKClient, decode_complete, get_algorithm_by_name
from jwt.exceptions import InvalidIssuerError, InvalidSignatureError
from oauthlib.oauth2.rfc6749.endpoints import AuthorizationEndpoint
from oauthlib.oauth2.rfc6749.endpoints import MetadataEndpoint
from oauthlib.oauth2.rfc6749.endpoints import TokenEndpoint
from oauthlib.oauth2.rfc6749.grant_types import AuthorizationCodeGrant
from requests_oauthlib import OAuth2Session
from secrets import compare_digest


from typing import Any, ClassVar, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from onegov.user.auth.provider import (
        HasApplicationIdAndNamespace, OIDCProvider)


@attrs(auto_attribs=True)
class OIDCAttributes:
    """
    Holds the expected OIDC claims.

    These claims may either be included in the JWT id token
    or in the response to the user endpoint
    """

    # the unique id in the OIDC provider
    source_id: str

    # The username (should be an email), use for User.username
    username: str

    # The users first name if available, use for User.realname
    first_name: str

    # The users last name if available, use for User.realname
    last_name: str

    # the name of the group
    group: str

    # Can be used if first / last name are not available to fill User.realname
    preferred_username: str

    @classmethod
    def from_cfg(cls, cfg: dict[str, Any]) -> Self:
        return cls(
            source_id=cfg.get('source_id', 'sub'),
            username=cfg.get('username', 'email'),
            group=cfg.get('group', 'group'),
            first_name=cfg.get('first_name', 'given_name'),
            last_name=cfg.get('last_name', 'family_name'),
            preferred_username='preferred_username'
        )


@attrs()
class OIDCClient:

    issuer: str = attrib()

    client_id: str = attrib()

    client_secret: str = attrib()

    button_text: str = attrib()

    # Needed attributes in the jwt token
    attributes: OIDCAttributes = attrib()

    primary: bool = attrib()

    # Required OAuth scope in addition to "openid"
    scope: list[str] = attrib(factory=list)

    # Override/amend discovered metadata
    fixed_metadata: dict[str, Any] = attrib(factory=dict)

    # FIXME: This is a little questionable if there's more than one
    #        OIDC provider for the same application. We should make
    #        this more robust
    _provider_metadata: ClassVar[dict[str, dict[str, Any]]] = {}

    def session(
        self,
        provider: OIDCProvider,
        request: CoreRequest,
        *,
        with_openid_scope: bool = False,
    ) -> OAuth2Session:
        """ Returns a requests session tied to a OAuth2 client """
        assert isinstance(self.scope, list), 'Invalid scope, expected list'
        provider_cls = type(provider)
        redirect_url = request.class_link(
            provider_cls, {'name': provider.name}, name='redirect')
        return OAuth2Session(
            self.client_id,
            scope=['openid', *self.scope] if with_openid_scope else self.scope,
            redirect_uri=redirect_url,
        )

    def metadata(self, request: CoreRequest) -> dict[str, Any]:
        metadata = self._provider_metadata.get(request.app.application_id)
        if metadata is None:
            # try to discover the metadata
            metadata_url = (self.issuer.rstrip('/')
                            + '/.well-known/oauth-authorization-server')
            try:
                response = requests.get(metadata_url, timeout=(5, 10))
                response.raise_for_status()
                claims = response.json()
                assert isinstance(claims, dict)
            except Exception:
                claims = {}

            claims.update(self.fixed_metadata)

            # The only endpoints we need our server to support for sure
            # are the authorization and token endpoints, so we pretend the
            # server only implements those, so that's the only thing we
            # validate
            # NOTE: Technically MetadataEndpoint will pull default values
            #       for these two endpoints, but since we don't currently
            #       use the affected properties, this should be fine.
            #       If we ever do end up using them, we may want to create
            #       a subclass so we only run the validation step.
            #       That should also allow us to get away without having
            #       to create these dummy endpoints
            endpoints = [AuthorizationEndpoint(
                'code',
                None,  # type: ignore[arg-type]
                {'code': AuthorizationCodeGrant(None)}
            ), TokenEndpoint(
                'authorization_code',
                None,  # type: ignore[arg-type]
                {'authorization_code': AuthorizationCodeGrant(None)}
            )]
            metadata = MetadataEndpoint(endpoints, claims).claims
            if 'jwks_uri' not in metadata:
                # TODO: Support manually specifying a static signing key?
                raise ValueError('key jwks_uri is a mandatory metadata.')
            if metadata['issuer'] != self.issuer:
                raise InvalidIssuerError(metadata['issuer'])
            # TODO: Should we make our own subclass that caches the JWK
            #       key set in redis rather than just in RAM?
            metadata['jwks_client'] = PyJWKClient(metadata['jwks_uri'])
            self._provider_metadata[request.app.application_id] = metadata
        return metadata

    def validate_token(
        self,
        request: CoreRequest,
        token: dict[str, Any]
    ) -> dict[str, Any]:

        metadata = self.metadata(request)
        access_token = token.get('access_token')
        id_token = token['id_token']
        jwks_client = metadata['jwks_client']
        signing_key = jwks_client.get_signing_key_from_jwt(id_token)
        # TODO: Should we provide some configurable leeway for exp?
        data = decode_complete(
            id_token,
            key=signing_key,
            audience=self.client_id,
            issuer=self.issuer,
            algorithms=metadata.get(
                'id_token_signing_alg_values_supported',
                ['RS256']
            ),
            # the following claims are required for OIDC
            options={'require': [
                'iss',
                'sub',
                'aud',
                'exp',
                'iat'
            ]}
        )
        header = data['header']
        payload = data['payload']

        if access_token and (given_at_hash := payload.get('at_hash')):
            # validate the access_token using at_hash
            alg = get_algorithm_by_name(header['alg'])
            digest = alg.compute_hash_digest(access_token.encode('utf-8'))
            at_hash = urlsafe_b64encode(digest[:len(digest) // 2])
            if not compare_digest(at_hash, given_at_hash.encode('utf-8')):
                raise InvalidSignatureError('given at_hash was incorrect')

        return payload


@attrs
class OIDCConnections:

    # instantiated connections for every tenant
    connections: dict[str, OIDCClient] = attrib()

    def client(self, app: HasApplicationIdAndNamespace) -> OIDCClient | None:
        if app.application_id in self.connections:
            return self.connections[app.application_id]

        if app.namespace in self.connections:
            return self.connections[app.namespace]
        return None

    @classmethod
    def from_cfg(cls, config: dict[str, Any]) -> Self:
        clients = {
            app_id: OIDCClient(
                issuer=cfg['issuer'],
                client_id=cfg['client_id'],
                client_secret=cfg['client_secret'],
                scope=cfg.get('scope', []),
                attributes=OIDCAttributes.from_cfg(
                    cfg.get('attributes', {})
                ),
                button_text=cfg['button_text'],
                primary=cfg.get('primary', False),
                fixed_metadata=cfg.get('fixed_metadata', {}),
            ) for app_id, cfg in config.items()
        }
        return cls(connections=clients)
