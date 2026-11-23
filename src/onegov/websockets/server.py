from asyncio import Future
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from functools import cached_property, partial
from http.cookies import SimpleCookie
from json import dumps, loads
from typing import TYPE_CHECKING, Any

from itsdangerous import BadSignature, Signer
from websockets.asyncio.server import broadcast, serve, ServerConnection

from onegov.core import cache
from onegov.core.browser_session import BrowserSession
from onegov.websockets import log
from onegov.websockets.utils import param_from_path

if TYPE_CHECKING:
    from collections.abc import Collection

    from websockets import Request, Response

    from onegov.core.types import JSONObject, JSONObject_ro
    from onegov.server.config import Config


CONNECTIONS: dict[str, set[WebSocketServer]] = {}
TOKEN = ''  # nosec: B105


class WebSocketServer(ServerConnection):
    """ A websocket server connection.

    This protocol handles multiple websocket applications:
    - Ticket notifications
    - Ticker
    """
    schema: str
    role: str | None
    groupids: frozenset[str]
    signed_session_id: str | None

    def __init__(
        self,
        config: Config | None,
        *args: Any,
        **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.config = config

    @cached_property
    def identity_secret(self) -> str:
        """ The identity secret, guaranteed to only be valid for the current
        application id.

        """
        return HKDF(
            algorithm=SHA256(),
            length=32,
            # NOTE: salt should generally be left blank or use pepper
            #       the better way to provide salt is to add it to info
            #       see: https://soatok.blog/2021/11/17/understanding-hkdf/
            salt=None,
            info=self.application_id.encode('utf-8') + b'+identity'
        ).derive(
            self.application_config['identity_secret'].encode('utf-8')
        ).hex()

    def unsign(self, text: str, salt: str = 'generic-signer') -> str | None:
        """ Unsigns a signed text, returning None if unsuccessful. """
        try:
            signer = Signer(self.identity_secret, salt=salt)
            return signer.unsign(text).decode('utf-8')
        except BadSignature:
            return None

    @cached_property
    def session_cache(self) -> cache.RedisCacheRegion:
        """ A cache that is kept for a long-ish time. """
        day = 60 * 60 * 24
        return cache.get(
            namespace=f'{self.application_id}:sessions',
            expiration_time=7 * day,
            redis_url=self.application_config.get('redis_url',
                                                  'redis://127.0.0.1:6379/0')
        )

    @cached_property
    def namespace(self) -> str:
        return self.schema.split('-', 1)[0]

    @cached_property
    def application_id(self) -> str:
        return '/'.join(self.schema.split('-', 1))

    @cached_property
    def application_config(self) -> dict[str, Any]:
        if self.config is None:
            return {}

        for c in self.config.applications:
            if c.namespace == self.namespace:
                return c.configuration

        return {}

    @cached_property
    def browser_session(self) -> BrowserSession | dict[str, Any]:
        if self.config is None or self.signed_session_id is None:
            return {}
        session_id = self.unsign(self.signed_session_id)
        if session_id is None:
            return {}
        return BrowserSession(
            cache=self.session_cache,
            token=session_id,
        )


def get_payload(
    message: str | bytes,
    expected: Collection[str]
) -> JSONObject | None:
    """ Deserialize JSON payload and check type. """

    try:
        payload = loads(message)
        assert payload['type'] in expected
        return payload
    except Exception:
        log.warning('Invalid payload received')
        return None


async def error(
    websocket: ServerConnection,
    message: str,
    close: bool = True
) -> None:
    """ Sends an error. """

    await websocket.send(
        dumps({
            'type': 'error',
            'message': message
        })
    )
    if close:
        await websocket.close()


async def acknowledge(websocket: ServerConnection) -> None:
    """ Sends an acknowledge. """

    await websocket.send(
        dumps({
            'type': 'acknowledged'
        })
    )


async def handle_listen(
    websocket: WebSocketServer,
    payload: JSONObject_ro
) -> None:
    """ Handles listening clients. """

    assert payload.get('type') == 'register'

    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return

    channel = payload.get('channel')
    if channel is not None and not isinstance(channel, str):
        await error(websocket, f'invalid channel: {channel}')
        return

    await acknowledge(websocket)

    schema_channel = f'{schema}-{channel}' if channel else schema
    log.debug(f'{websocket.id} listens @ {schema_channel}')
    connections = CONNECTIONS.setdefault(schema_channel, set())
    connections.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        connections = CONNECTIONS.setdefault(schema_channel, set())
        if websocket in connections:
            connections.remove(websocket)


async def handle_authentication(
    websocket: ServerConnection,
    payload: JSONObject_ro
) -> None:
    """ Handles authentication. """

    assert payload.get('type') == 'authenticate'

    token = payload.get('token')
    if not token or not isinstance(token, str):
        await error(websocket, 'invalid token')
        return
    if token != TOKEN:
        await error(websocket, 'authentication failed')
        return

    await acknowledge(websocket)

    log.debug(f'{websocket.id} authenticated')


async def handle_status(
    websocket: WebSocketServer,
    payload: JSONObject_ro
) -> None:
    """ Handles status requests. """

    assert payload.get('type') == 'status'

    await acknowledge(websocket)

    await websocket.send(
        dumps({
            'type': 'status',
            'message': {
                'connections': {
                    key: len(values)
                    for key, values in CONNECTIONS.items()
                }
            }
        })
    )

    log.debug(f'{websocket.id} status sent')


async def handle_broadcast(
    websocket: WebSocketServer,
    payload: JSONObject_ro
) -> None:
    """ Handles broadcasts. """

    assert payload.get('type') == 'broadcast'

    message = payload.get('message')
    schema = payload.get('schema')
    channel = payload.get('channel')
    groupids = payload.get('groupids')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return
    if channel is not None and not isinstance(channel, str):
        await error(websocket, f'invalid channel: {channel}')
        return
    if not message:
        await error(websocket, 'missing message')
        return

    await acknowledge(websocket)

    schema_channel = f'{schema}-{channel}' if channel else schema
    connections = CONNECTIONS.get(schema_channel, set())
    if isinstance(groupids, list):
        connections = {
            connection
            for connection in connections
            if connection.role == 'admin'
            or not connection.groupids.isdisjoint(groupids)
        }
    if connections:
        broadcast(
            connections,
            dumps({
                'type': 'notification',
                'message': message
            })
        )

    log.debug(
        f'{websocket.id} sent {message}'
        f' to {len(connections)} receiver(s) @ {schema_channel}'
    )


async def handle_manage(
    websocket: WebSocketServer,
    authentication_payload: JSONObject_ro
) -> None:
    """ Handles managing clients. """

    await handle_authentication(websocket, authentication_payload)

    async for message in websocket:
        payload = get_payload(message, ('broadcast', 'status'))
        if payload and payload['type'] == 'broadcast':
            await handle_broadcast(websocket, payload)
        elif payload and payload['type'] == 'status':
            await handle_status(websocket, payload)
        else:
            await error(
                websocket,
                # FIXME: technically message can be bytes
                f'invalid command: {message}'  # type:ignore
            )


async def handle_start(websocket: ServerConnection) -> None:
    assert isinstance(websocket, WebSocketServer)
    log.debug(f'{websocket.id} connected')
    message = await websocket.recv()
    payload = get_payload(message, ('authenticate', 'register'))
    if payload and payload['type'] == 'authenticate':
        await handle_manage(websocket, payload)
    elif payload and payload['type'] == 'register':
        await handle_listen(websocket, payload)
    else:
        # FIXME: technically message can be bytes
        await error(websocket, f'invalid command: {message}')  # type:ignore
    log.debug(f'{websocket.id} disconnected')


def process_request(
    self: ServerConnection,
    request: Request
) -> Response | None:
    """ Intercept initial HTTP request.

    Before establishing a WebSocket connection, a client sends a HTTP
    request to "upgrade" the connection to a WebSocket connection. We use
    this to identify the browser session (if any), so we can filter
    broadcasts by role and group.
    """
    assert isinstance(self, WebSocketServer)

    try:
        cookie = SimpleCookie(request.headers.get_all('Cookie')[0])
        session_id = cookie['session_id'].value
    except IndexError:
        session_id = None

    self.signed_session_id = session_id

    try:
        self.schema = param_from_path('schema', request.path)
    except ValueError:
        # FIXME: This should only happen for internal message sent through
        #        the management channel, ideally we route those through
        #        a different path, so we can keep this validation for user
        #        connections.
        return None

    # browser_session requires self.schema
    self.role = self.browser_session.get('role')
    self.groupids = self.browser_session.get('groupids', frozenset())

    return None


async def main(
    host: str, port: int, token: str,
    config: Config | None = None
) -> None:

    global TOKEN
    TOKEN = token
    log.debug(f'Serving on ws://{host}:{port}')

    # TODO: Pass in valid origins. Is there already a list of allowed
    # origins?
    async with serve(handle_start, host, port,
                     process_request=process_request,
                     create_connection=partial(WebSocketServer, config)):  # type: ignore[arg-type]
        await Future()
