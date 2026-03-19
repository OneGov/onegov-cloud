from __future__ import annotations

import morepath

from attr import attrs, attrib
from dogpile.cache.api import NO_VALUE
from hashlib import blake2b
from onegov.user import log
from onegov.user.auth import Auth
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.cache import Cache
from saml2.client import Saml2Client as Connection
from saml2.config import Config
from saml2.ident import code, decode
from saml2.mdstore import locations
from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.s_utils import status_message_factory
from saml2.s_utils import success_status_factory
from saml2.samlp import STATUS_REQUEST_DENIED
from saml2.samlp import STATUS_UNKNOWN_PRINCIPAL


from typing import overload, Any, Self, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.cache import RedisCacheRegion
    from onegov.core.framework import Framework
    from onegov.core.request import CoreRequest
    from onegov.user import User, UserApp
    from onegov.user.auth.provider import (
        HasApplicationIdAndNamespace, SAML2Provider)
    from webob import Response


def handle_logout_request(
    conn: Connection,
    name_id: str | None,
    logout_req: Any,
    relay_state: str | None
) -> tuple[bool, Any]:
    # we re-implement conn.handle_logout_request so we can handle
    # error states more gracefully and so we can always force a
    # redirect binding to be used
    supported_bindings = [BINDING_HTTP_REDIRECT]
    success = False
    if logout_req.message.name_id == name_id:
        try:
            if conn.local_logout(name_id):
                status = success_status_factory()
                success = True
            else:
                status = status_message_factory(
                    'Server error', STATUS_REQUEST_DENIED)
        except KeyError:
            status = status_message_factory(
                'Server error', STATUS_REQUEST_DENIED)
    else:
        status = status_message_factory(
            'Wrong user', STATUS_UNKNOWN_PRINCIPAL)

    # construct the LogoutResponse
    args = conn.response_args(logout_req.message, supported_bindings)
    response = conn.create_logout_response(
        logout_req.message, bindings=supported_bindings, status=status)

    request_info = conn.apply_binding(
        args['binding'], response, args['destination'], relay_state,
        response=True)
    return success, request_info


def finish_logout(
    request: CoreRequest,
    user: User,
    to: str,
    local: bool = True
) -> Response:
    # this always finishes the SAML2 logout, but it may delay
    # the local logout and make it the regular logout view's
    # responsibility
    assert user
    if user.data:
        # remove the saml2 session data
        user.data.pop('saml2_transient_id', None)
        user.data.pop('saml2_not_on_or_after', None)
    if local:
        user.remove_current_session(request)

    response = morepath.redirect(to)
    if local:
        request.app.forget_identity(response, request)

    return response


@attrs(auto_attribs=True)
class SAML2Attributes:
    """ Holds the required SAML2 Attributes """

    # the globally unique id
    source_id: str

    # name for the username in User
    username: str

    # The users first name if available, use for User.realname
    first_name: str

    # The users last name if available, use for User.realname
    last_name: str

    # the name of the groups per tenant id, groups roles or scp
    groups: str

    @classmethod
    def from_cfg(cls, cfg: dict[str, Any]) -> Self:
        return cls(
            source_id=cfg.get('source_id', 'uid'),
            username=cfg.get('username', 'email'),
            first_name=cfg.get('first_name', 'givenName'),
            last_name=cfg.get('last_name', 'sn'),
            groups=cfg.get('groups', 'member'),
        )


@attrs()
class SAML2Client:

    metadata: str = attrib()
    """ Paths to the relevant idp metadata XML files """

    button_text: str = attrib()
    """ Text to show on login button """

    treat_as_ldap: bool = attrib()
    """ Whether or not users created by this provider should show up
    as being created by LDAP instead. Necessary when using LDAP to
    sync the users periodically and deactivate old accounts. """

    want_response_signed: bool = attrib()
    """ Whether the response from the IdP should be signed """

    attributes: SAML2Attributes = attrib()
    """ Mapping of attribute names """

    primary: bool = attrib()
    """ Whether or not this is the primary login provider """

    slo_enabled: bool = attrib(default=True)
    """ Whether or not to enable the SLO service """

    client_key_file: str | None = attrib(default=None)
    """ Path to the client key for signing requests. """

    client_cert_file: str | None = attrib(default=None)
    """ Path to the client certifcate for signing requests. """

    _connections: dict[str, Connection] = attrib(factory=dict, init=False)

    def get_binding(self, request: CoreRequest) -> str:
        if request.method == 'GET':
            return BINDING_HTTP_REDIRECT
        elif request.method == 'POST':
            return BINDING_HTTP_POST
        else:
            raise NotImplementedError()

    def get_sessions(self, app: UserApp | Framework) -> Mangled:
        # this can use our short-lived cache, it will likely
        # be deleted before it can expire anyways
        return Mangled(app.cache, 'saml2_sessions')

    def get_redirects(self, app: UserApp | Framework) -> Mangled:
        # same here
        return Mangled(app.cache, 'saml2_redirects')

    def connection(
        self,
        provider: SAML2Provider,
        request: CoreRequest
    ) -> Connection:
        """ Returns the SAML2 instance """
        # NOTE: Unfortunately we can't create all the connections
        #       at application start up so we won't know about
        #       configuration errors until a login attempt is made
        #       Maybe we try to create a dummy configuration first
        #       to make sure the IdP XML is fine?
        conn = self._connections.get(request.app.application_id)
        if conn is None:
            # create connection
            try:
                base_url = request.application_url.rstrip('/')
                provider_cls = type(provider)
                acs_url = request.class_link(
                    provider_cls, {'name': provider.name}, name='redirect')
                slo_url = request.class_link(
                    provider_cls, {'name': provider.name}, name='logout')
                saml_settings: dict[str, Any] = {
                    # TODO: Support metadata via remote/mdq, multiple idp?
                    'entityid': base_url,
                    'metadata': {'local': [self.metadata]},
                    'service': {
                        'sp': {
                            'endpoints': {
                                'assertion_consumer_service': [
                                    (acs_url, BINDING_HTTP_REDIRECT),
                                    (acs_url, BINDING_HTTP_POST)
                                ],
                            },
                            'name_id_format': [NAMEID_FORMAT_TRANSIENT],
                            'required_attributes': [
                                self.attributes.source_id,
                                self.attributes.username,
                                self.attributes.groups
                            ],
                            'optional_attributes': [
                                self.attributes.first_name,
                                self.attributes.last_name,
                            ],
                            'want_response_signed': self.want_response_signed,
                            'allow_unsolicited': False,
                        },
                    },
                }

                if self.slo_enabled:
                    saml_settings['service']['sp']['endpoints'][
                        'single_logout_service'
                    ] = [
                        (slo_url, BINDING_HTTP_REDIRECT),
                        (slo_url, BINDING_HTTP_POST)
                    ]

                if self.client_key_file and self.client_cert_file:
                    saml_settings['key_file'] = self.client_key_file
                    saml_settings['cert_file'] = self.client_cert_file
                    saml_settings['signing_algorithm'] = (
                        'http://www.w3.org/2001/04/xmldsig-more#rsa-sha512')
                    saml_settings['digest_algorithm'] = (
                        'http://www.w3.org/2001/04/xmlenc#sha512')
                    sp_settings = saml_settings['service']['sp']
                    sp_settings['authn_requests_signed'] = True
                    sp_settings['logout_requests_signed'] = True
                    sp_settings['logout_responses_signed'] = True

                config = Config()
                config.load(saml_settings)
                identity_cache = IdentityCache(request.app)
                # the state cache can be short-lived
                state_cache = Mangled(request.app.cache, 'saml2_state')
                conn = Connection(
                    config=config,
                    identity_cache=identity_cache,
                    state_cache=state_cache
                )
                self._connections[request.app.application_id] = conn
            except Exception as exception:
                raise ValueError(
                    f'SAML2 config error: {exception!s}'
                ) from exception
        return conn

    def get_name_id(self, user: User | None) -> str | None:
        if user and user.data:
            return user.data.get('saml2_transient_id')
        return None

    def create_logout_request(
        self,
        provider: SAML2Provider,
        request: CoreRequest,
        user: User | None
    ) -> tuple[str | None, Any | None]:
        transient_id = self.get_name_id(user)
        if not transient_id:
            return None, None

        # FIXME: Unfortunately the convenience method `global_logout`
        #        does not return the request_id for the responses it
        #        generates, so theres no way to store any locale state
        #        that should belong to that request, like e.g. the
        #        `to` clause from the logout, so we have to re-implement
        #        global logout. This is not a full implementation, as it
        #        always attempts a redirect, regardless of what may be
        #        configured. It also assumes that there is only one IdP
        conn = self.connection(provider, request)
        name_id = decode(transient_id)
        entity_ids = conn.users.issuers_of_info(name_id)
        if not entity_ids:
            # nothing to do
            return None, None

        # disregard any IdP beyond the first one
        entity_id = entity_ids[0]
        bindings = conn.metadata.single_logout_service(
            entity_id=entity_id, typ='idpsso')

        # we only support redirects for now
        if BINDING_HTTP_REDIRECT not in bindings:
            return None, None

        service_info = bindings[BINDING_HTTP_REDIRECT]
        service_location = next(locations(service_info), None)
        if not service_location:
            # we can't redirect without a location
            log.warning('SAML2: No location configured for IdP SSO')
            return None, None

        try:
            session_info = conn.users.get_info_from(name_id, entity_id, False)
            session_index = session_info.get('session_index')
            session_indexes = [session_index] if session_index else None
        except KeyError:
            session_indexes = None

        # TODO: This would need to change to support signed requests
        session_id, logout_req = conn.create_logout_request(
            service_location,
            entity_id,
            name_id=name_id,
            session_indexes=session_indexes)
        relay_state = conn._relay_state(session_id)
        request_info = conn.apply_binding(
            BINDING_HTTP_REDIRECT,
            str(logout_req),
            service_location,
            relay_state)

        # remember this logout request
        conn.state[session_id] = {
            'entity_id': entity_id,
            'operation': 'SLO',
            'entity_ids': entity_ids,
            'name_id': code(name_id),
            'reason': '',
            'not_on_or_after': None,
            'sign': False,
        }
        return session_id, request_info

    def handle_slo(
        self,
        provider: SAML2Provider,
        request: CoreRequest
    ) -> Response:

        # this could be either a request or a response
        saml_request = request.params.get('SAMLRequest')
        saml_response = request.params.get('SAMLResponse')
        # FIXME: This depends on OrgRequest, we should refactor this
        user = request.current_user  # type:ignore
        to = request.browser_session.pop('logout_to', provider.to or '/')
        if saml_request:
            # this should be a LogoutRequest
            conn = self.connection(provider, request)
            transient_id = self.get_name_id(user)
            binding = self.get_binding(request)
            _relay_state = request.params.get('RelayState')
            if isinstance(_relay_state, str):
                relay_state = _relay_state
            else:
                relay_state = None
            logout_req = conn.parse_logout_request(saml_request, binding)
            success, request_info = handle_logout_request(
                conn, transient_id, logout_req, relay_state)
            # all we care about is the location header
            headers = {k.lower(): v for k, v in request_info['headers']}
            if success:
                # we need to finish the local logout
                return finish_logout(request, user, headers['location'])
            else:
                # in this case we only need to redirect
                return morepath.redirect(headers['location'])

        elif saml_response:
            # this should be a LogoutResponse, either way we finish
            # the local logout
            conn = self.connection(provider, request)
            binding = self.get_binding(request)
            try:
                logout_res = conn.parse_logout_request_response(
                    saml_response, binding)

                # recover redirect target
                session_id = logout_res.in_response_to
                redirects = self.get_redirects(request.app)
                to = redirects.get(session_id, to)

                # TODO: If we want to support multiple IdP's this may
                #       result in further redirects to the next IdP
                #       for now we assume this doesn't happen, if we
                #       ever do we need to implement this method our-
                #       selves because the method won't properly remove
                #       the IdP from the list of IdPs to disconnect from
                conn.handle_logout_response(logout_res)

            except Exception as exc:
                # We ignore any exceptions in handling the LogoutResponse
                # because we want to finish the logout either way!
                log.warning(f'Error in handling LogoutResponse: {exc}')

        # if we got neither a response nor a request we just logout
        # the same way we would if we got a response, i.e. we terminate
        # the SAML2 session and redirect back to the logout view to
        # finish local logout
        if user:
            # first we terminate the SAML2 session and then we redirect
            # to the normal logout view to finish the local logout
            logout_url = request.class_link(Auth, {'to': to}, name='logout')
            return finish_logout(request, user, logout_url, local=False)

        else:
            # if we're not logged in we just redirect to the logout_to
            # because we're already logged out, so we're not allowed to
            # access the logout view.
            return morepath.redirect(request.transform(to))


@attrs
class SAML2Connections:

    # instantiated connections for every tenant
    connections: dict[str, SAML2Client] = attrib()

    def client(
        self,
        app: HasApplicationIdAndNamespace
    ) -> SAML2Client | None:
        if app.application_id in self.connections:
            return self.connections[app.application_id]

        if app.namespace in self.connections:
            return self.connections[app.namespace]

        return None

    @classmethod
    def from_cfg(cls, config: dict[str, Any]) -> Self:
        clients = {
            app_id: SAML2Client(
                metadata=cfg['metadata'],
                button_text=cfg['button_text'],
                treat_as_ldap=cfg.get('treat_as_ldap', False),
                want_response_signed=cfg.get('want_resonse_signed', True),
                attributes=SAML2Attributes.from_cfg(
                    cfg.get('attributes', {})),
                primary=cfg.get('primary', False),
                slo_enabled=cfg.get('slo_enabled', True),
                client_key_file=cfg.get('client_key_file', None),
                client_cert_file=cfg.get('client_cert_file', None),
            ) for app_id, cfg in config.items()
        }
        return cls(connections=clients)


class Mangled:
    """
    Dict like interface that mangles the name_id that gets passed into the
    cache, so valid name_ids cannot be discovered through key listing
    """

    def __init__(self, cache: RedisCacheRegion, prefix: str = ''):
        self._cache = cache
        self._prefix = prefix

    def mangle(self, name_id: str) -> str:
        return blake2b(
            (self._prefix + name_id).encode('utf-8'),
            digest_size=24).hexdigest()

    @overload
    def get(self, name_id: str, default: None = None) -> Any | None: ...
    @overload
    def get(self, name_id: str, default: Any) -> Any: ...

    def get(self, name_id: str, default: Any = None) -> Any | None:
        value = self._cache.get(self.mangle(name_id))
        if value is NO_VALUE:
            return default
        return value

    @overload
    def pop(self, name_id: str) -> Any: ...
    @overload
    def pop(self, name_id: str, default: None) -> Any | None: ...
    @overload
    def pop(self, name_id: str, default: Any) -> Any: ...

    def pop(self, name_id: str, default: Any = NO_VALUE) -> Any | None:
        key = self.mangle(name_id)
        value = self._cache.get(key)
        if value is NO_VALUE:
            if default is NO_VALUE:
                raise KeyError
            return default
        # delete the value from the cache
        self._cache.delete(key)
        return value

    def __getitem__(self, name_id: str) -> Any:
        value = self._cache.get(self.mangle(name_id))
        if value is NO_VALUE:
            raise KeyError
        return value

    def __setitem__(self, name_id: str, value: Any) -> None:
        self._cache.set(self.mangle(name_id), value)

    def __delitem__(self, name_id: str) -> None:
        self._cache.delete(self.mangle(name_id))

    def __contains__(self, name_id: str) -> bool:
        return self._cache.get(self.mangle(name_id)) is not NO_VALUE


class IdentityCache(Cache):  # type:ignore[misc]
    """
    Extension to the dict/shelve based default cache to use our
    redis based dogpile cache instead
    """

    def __init__(self, app: Framework):
        # for now we use the same expiration time as our session cache
        # we want to be able to initiate a SLO as long as the user is
        # logged in, so we need the identity to remain cached for at
        # least that long
        # TODO: Does the expiration time of browser session get reset
        #       every time a value changes? If so, maybe this cache
        #       should live even longer? Is the absolute lifetime of
        #       a user session defined somewhere?
        cache = app.get_cache('saml2', expiration_time=7 * 60 * 60 * 24)
        self._db = Mangled(cache)
        self._sync = False

    def set(
        self,
        name_id: str,
        entity_id: str,
        info: dict[str, Any],
        not_on_or_after: int = 0
    ) -> None:
        # We need to re-implement due to how dogpile handles mutable objects
        info = dict(info)
        cni = code(name_id)
        if 'name_id' in info:
            # make friendly to serialization
            info['name_id'] = cni

        entities = self._db.get(cni, {})
        entities[entity_id] = (not_on_or_after, info)
        self._db[cni] = entities
