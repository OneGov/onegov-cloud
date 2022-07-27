import morepath

from typing import Dict

from attr import attrs, attrib
from dogpile.cache.api import NO_VALUE
from hashlib import blake2b
from onegov.user import log
from onegov.user.auth import Auth
from saml2 import BINDING_HTTP_POST, BINDING_HTTP_REDIRECT
from saml2.cache import Cache
from saml2.client import Saml2Client as Connection
from saml2.client_base import LogoutError
from saml2.config import Config
from saml2.ident import code
from saml2.saml import NAMEID_FORMAT_TRANSIENT
from saml2.s_utils import status_message_factory
from saml2.s_utils import success_status_factory
from saml2.samlp import STATUS_REQUEST_DENIED
from saml2.samlp import STATUS_UNKNOWN_PRINCIPAL


def handle_logout_request(conn, name_id, logout_req, relay_state):
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
                    "Server error", STATUS_REQUEST_DENIED)
        except KeyError:
            status = status_message_factory(
                "Server error", STATUS_REQUEST_DENIED)
    else:
        status = status_message_factory(
            "Wrong user", STATUS_UNKNOWN_PRINCIPAL)

    # construct the LogoutResponse
    args = conn.response_args(logout_req.message, supported_bindings)
    response = conn.create_logout_response(
        logout_req.message, bindings=supported_bindings, status=status)

    request_info = conn.apply_binding(
        args['binding'], response, args['destination'], relay_state,
        response=True)
    return success, request_info


def finish_logout(request, user, to, local=True):
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
class SAML2Attributes(object):
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
    def from_cfg(cls, cfg):
        return cls(
            source_id=cfg.get('source_id', 'uid'),
            username=cfg.get('username', 'email'),
            first_name=cfg.get('first_name', 'givenName'),
            last_name=cfg.get('last_name', 'sn'),
            groups=cfg.get('groups', 'member'),
        )


@attrs()
class SAML2Client():

    metadata: str = attrib()
    """ Paths to the relevant idp metadata XML files """

    button_text: str = attrib()
    """ Text to show on login button """

    treat_as_ldap: bool = attrib()
    """ Whether or not users created by this provider should show up
    as being created by LDAP instead. Necessary when using LDAP to
    sync the users periodically and deactivate old accounts. """

    want_resonse_signed: bool = attrib()
    """ Whether the response from the IdP should be signed """

    attributes: SAML2Attributes = attrib()
    """ Mapping of attribute names """

    _connections = {}

    def get_binding(self, request):
        if request.method == 'GET':
            return BINDING_HTTP_REDIRECT
        elif request.method == 'POST':
            return BINDING_HTTP_POST
        else:
            assert False, "binding not implemented"

    def get_sessions(self, app):
        # this can use our short-lived cache, it will likely
        # be deleted before it can expire anyways
        return Mangled(app.cache, 'saml2_sessions')

    def get_redirects(self, app):
        # same here
        return Mangled(app.cache, 'saml2_redirects')

    def connection(self, provider, request):
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
                base_url = request.application_url
                provider_cls = type(provider)
                acs_url = request.class_link(
                    provider_cls, {'name': provider.name}, name='redirect')
                slo_url = request.class_link(
                    provider_cls, {'name': provider.name}, name='logout')
                saml_settings = {
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
                                'single_logout_service': [
                                    (slo_url, BINDING_HTTP_REDIRECT),
                                    (slo_url, BINDING_HTTP_POST)
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
                            'want_response_signed': self.want_resonse_signed,
                            'allow_unsolicited': False,
                        },
                    },
                }

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
            except Exception as e:
                raise ValueError(
                    f'SAML2 config error: {str(e)}')
        return conn

    def get_name_id(self, user):  
        if user and user.data:
            return user.data.get('saml2_transient_id')

    def logout_url(self, provider, request, user):
        transient_id = self.get_name_id(user)
        if not transient_id:
            return None

        conn = self.connection(provider, request)
        try:
            data = conn.global_logout(transient_id)
        except LogoutError:
            return None

        for entity_id, logout_info in data.items():
            if not isinstance(logout_info, tuple):
                # safe to ignore
                continue

            binding, request_info = logout_info
            if binding != BINDING_HTTP_REDIRECT:
                # we only support redirect bindings for now
                continue

            # all we care about is the location header
            headers = {k.lower(): v for k, v in request_info['headers']}
            return headers.get('location', None)

    def handle_slo(self, provider, request):
        # this could be either a request or a response
        saml_request = request.params.get('SAMLRequest')
        saml_response = request.params.get('SAMLResponse')
        user = request.current_user
        if saml_request:
            # this should be a LogoutRequest
            conn = self.connection(provider, request)
            transient_id = self.get_name_id(user)
            binding = self.get_binding(request)
            relay_state = request.params.get('RelayState')
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
        to = request.browser_session.pop('logout_to', provider.to or '/')

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
class SAML2Connections():

    # instantiated connections for every tenant
    connections: Dict[str, SAML2Client] = attrib()

    def client(self, app):
        if app.application_id in self.connections:
            return self.connections[app.application_id]

        if app.namespace in self.connections:
            return self.connections[app.namespace]

    @classmethod
    def from_cfg(cls, config):
        clients = {
            app_id: SAML2Client(
                metadata=cfg['metadata'],
                button_text=cfg['button_text'],
                treat_as_ldap=cfg.get('treat_as_ldap', False),
                want_resonse_signed=cfg.get('want_resonse_signed', True),
                attributes=SAML2Attributes.from_cfg(
                    cfg.get('attributes', {}))
            ) for app_id, cfg in config.items()
        }
        return cls(connections=clients)


class Mangled():
    """
    Dict like interface that mangles the name_id that gets passed into the
    cache, so valid name_ids cannot be discovered through key listing
    """

    def __init__(self, cache, prefix=''):
        self._cache = cache
        self._prefix = prefix

    def mangle(self, name_id):
        return blake2b(
            (self._prefix + name_id).encode('utf-8'),
            digest_size=24).hexdigest()

    def get(self, name_id, default=None):
        value = self._cache.get(self.mangle(name_id))
        if value is NO_VALUE:
            return default
        return value

    def pop(self, name_id, default=NO_VALUE):
        key = self.mangle(name_id)
        value = self._cache.get(key)
        if value is NO_VALUE:
            if default is NO_VALUE:
                raise KeyError
            return default
        # delete the value from the cache
        self._cache.delete(key)
        return value

    def __getitem__(self, name_id):
        value = self._cache.get(self.mangle(name_id))
        if value is NO_VALUE:
            raise KeyError
        return value

    def __setitem__(self, name_id, value):
        self._cache.set(self.mangle(name_id), value)

    def __delitem__(self, name_id):
        self._cache.delete(self.mangle(name_id))

    def __contains__(self, name_id):
        return self._cache.get(self.mangle(name_id)) is not NO_VALUE


class IdentityCache(Cache):
    """
    Extension to the dict/shelve based default cache to use our
    redis based dogpile cache instead
    """

    def __init__(self, app):
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

    def set(self, name_id, entity_id, info, not_on_or_after=0):
        # We need to re-implement due to how dogpile handles mutable objects
        info = dict(info)
        cni = code(name_id)
        if 'name_id' in info:
            # make friendly to serialization
            info['name_id'] = cni

        entities = self._db.get(cni, {})
        entities[entity_id] = (not_on_or_after, info)
        self._db[cni] = entities
