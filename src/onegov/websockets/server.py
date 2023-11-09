import hashlib

from asyncio import Future
from itsdangerous import BadSignature, Signer
from json import dumps
from json import loads
from functools import cached_property, partial
from onegov.websockets import log
from websockets.legacy.protocol import broadcast
from websockets.legacy.server import serve, WebSocketServerProtocol
from onegov.core import cache

from onegov.user import User, UserCollection
from onegov.chat.collections import ChatCollection
from onegov.core.orm import SessionManager, Base
from onegov.core.browser_session import BrowserSession
from http.cookies import SimpleCookie


from typing import TYPE_CHECKING, Any
if TYPE_CHECKING:
    from collections.abc import Collection
    from onegov.core.types import JSONObject
    from onegov.core.types import JSONObject_ro
    from sqlalchemy.orm import Session
    from uuid import UUID
    from onegov.chat.models import Chat
    from collections.abc import Mapping


CONNECTIONS: dict[str, set[WebSocketServerProtocol]] = {}
TOKEN = ''  # nosec: B105

NOTFOUND = object()
SESSIONS: dict[str, 'Session'] = {}
STAFF_CONNECTIONS: dict[str, set[WebSocketServerProtocol]] = {}
STAFF: dict[str, dict['UUID', User]] = {}  # For Authentication of User
CHATS: dict[str, dict['UUID', 'Chat']] = {}  # For DB
# For Messages
CHANNELS: dict[str, dict[str, set[WebSocketServerProtocol]]] = {}


class WebSocketServer(WebSocketServerProtocol):
    schema:str
    signed_session_id:str

    def __init__(self, config, session_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.session_manager = session_manager

    def unsign(self, text: str) -> str | None:
        """ Unsigns a signed text, returning None if unsuccessful. """
        identity_secret = self.application_config[
            'identity_secret'] + self.application_id_hash
        try:
            signer = Signer(identity_secret, salt='generic-signer')
            return signer.unsign(text).decode('utf-8')
        except BadSignature:
            return None

    async def process_request(self, path, headers):
        morsel = SimpleCookie(headers.get("Cookie", "")).get('session_id')
        self.signed_session_id = morsel.value if morsel else None

    async def get_chat(self, id):
        chat = CHATS.setdefault(self.schema, {}).get(id, NOTFOUND)
        if chat is NOTFOUND:
            chat = ChatCollection(self.session).by_id(id)
            if chat and not chat.active:
                chat = None
            CHATS[self.schema][chat.id] = chat
        return chat

    @property
    def session(self):
        session = SESSIONS.get(self.schema)
        if session is None:
            self.session_manager.set_current_schema(self.schema)
            session = SESSIONS[self.schema] = self.session_manager.session()
            STAFF[self.schema] = {user.id: user for user in UserCollection(
                session).query().filter(User.role.in_(['editor', 'admin']))}
            CHATS[self.schema] = {}
        return session

    @property
    def application_id_hash(self) -> str:
        """ The application_id as hash, use this if the application_id can
        be read by the user -> this obfuscates things slightly.

        """
        # sha-1 should be enough, because even if somebody was able to get
        # the cleartext value I honestly couldn't tell you what it could be
        # used for ...
        return hashlib.new(  # nosec: B324
            'sha1',
            self.application_id.encode('utf-8'),
            usedforsecurity=False
        ).hexdigest()

    @property
    def session_cache(self) -> cache.RedisCacheRegion:
        """ A cache that is kept for a long-ish time. """
        day = 60 * 60 * 24
        return cache.get(
            namespace=f'{self.application_id}:sessions',
            expiration_time=7 * day,
            redis_url=self.application_config.get('redis_url',
                                                  'redis://127.0.0.1:6379/0')
        )

    @property
    def namespace(self):
        return self.schema.split('-', 1)[0]

    @property
    def application_id(self):
        return '/'.join(self.schema.split('-', 1))

    @property
    def application_config(self):
        for c in self.config.applications:
            if c.namespace == self.namespace:
                return c.configuration

    @cached_property
    def browser_session(self) -> 'Mapping [str, Any]':

        if self.signed_session_id is None:
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
    expected: 'Collection[str]'
) -> 'JSONObject | None':
    """ Deserialize JSON payload and check type. """

    try:
        payload = loads(message)
        assert payload['type'] in expected
        return payload
    except Exception:
        log.warning('Invalid payload received')
        return None


async def error(
    websocket: WebSocketServerProtocol,
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


async def acknowledge(websocket: WebSocketServerProtocol) -> None:
    """ Sends an acknowledge. """

    await websocket.send(
        dumps({
            'type': 'acknowledged'
        })
    )


async def handle_listen(
    websocket: WebSocketServerProtocol,
    payload: 'JSONObject_ro'
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
    websocket: WebSocketServerProtocol,
    payload: 'JSONObject_ro'
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
    websocket: WebSocketServerProtocol,
    payload: 'JSONObject_ro'
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
    websocket: WebSocketServerProtocol,
    payload: 'JSONObject_ro'
) -> None:
    """ Handles broadcasts. """

    assert payload.get('type') == 'broadcast'

    message = payload.get('message')
    schema = payload.get('schema')
    channel = payload.get('channel')
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
    websocket: WebSocketServerProtocol,
    authentication_payload: 'JSONObject_ro'
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


async def handle_customer_chat(websocket: WebSocketServerProtocol, payload):
    """
    Starts a chat. Handles listening to messages on channel.
    """

    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return

    websocket.schema = schema  # For DB Connection
    channel = websocket.browser_session.get("active_chat_id")

# Alles nochher för t DB
    await websocket.get_chat(channel)
    # # log.debug(f'CHATS: {CHATS}')
    # # log.debug(f'STAFF: {STAFF}')

    await acknowledge(websocket)

    all_channels = CHANNELS.setdefault(schema, {})
    channel_connections = all_channels.setdefault(channel.hex, set())
    channel_connections.add(websocket)
    staff_connections = STAFF_CONNECTIONS.setdefault(schema, set())

    log.debug(f'added {websocket.id} to channel-connections')
    log.debug(f'ws-location: {websocket}')
    # log.debug(f'CHANNELS: {CHANNELS}')

    for client in staff_connections:
        await client.send(dumps({
            'type': "notification",
            'message': dumps({
                'type': 'info',
                'text': 'Neue Chat-Anfrage',
                'channel': channel.hex
            })
        }))

    while websocket.open:
        try:
            message = await websocket.recv()
            log.debug(f'customer {websocket.id} got the message {message}')
            log.debug(f'known channel members {channel_connections}')
        except Exception:
            channel_connections.remove(websocket)
            log.debug(f'removed {websocket.id} from channel-connections')

        for client in channel_connections:
            await client.send(dumps({
                'type': "notification",
                'message': message
            }))

        websocket.session.flush()


async def handle_staff_chat(websocket: WebSocketServerProtocol, payload):
    """
    Registers staff member and listens to messages.
    """

    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return

    websocket.schema = schema  # For DB Connection

# Alles nochher för t DB
    # await websocket.get_chat(channel)
    # # log.debug(f'CHATS: {CHATS}')
    # # log.debug(f'STAFF: {STAFF}')

    await acknowledge(websocket)

    all_channels = CHANNELS.setdefault(schema, {})
    staff_connections = STAFF_CONNECTIONS.setdefault(schema, set())
    staff_connections.add(websocket)

    log.debug(f'added {websocket.id} to staff-connections')

    while websocket.open:
        try:
            message = await websocket.recv()
            log.debug(f'staff member {websocket.id} got the message {message}')

        except Exception:
            staff_connections.remove(websocket)
            log.debug(f'removed {websocket.id} from staff-connections')

        if loads(message)['type'] == 'accepted':
            open_channel = loads(message)['channel']
            channel_clients = all_channels[open_channel]
            channel_clients.add(websocket)

        for client in channel_clients:
            await client.send(dumps({
                'type': "notification",
                'message': message,
            }))

    websocket.session.flush()


async def handle_start(websocket: WebSocketServerProtocol) -> None:
    log.debug(f'{websocket.id} connected')
    message = await websocket.recv()
    payload = get_payload(message, ('authenticate', 'register',
                                    'customer_chat','staff_chat'))
    if payload and payload['type'] == 'authenticate':
        await handle_manage(websocket, payload)
    elif payload and payload['type'] == 'register':
        await handle_listen(websocket, payload)
    elif payload and (payload['type'] == 'customer_chat'):
        await handle_customer_chat(websocket, payload)
    elif payload and (payload['type'] == 'staff_chat'):
        await handle_staff_chat(websocket, payload)
    else:
        # FIXME: technically message can be bytes
        await error(websocket, f'invalid command: {message}')  # type:ignore
    log.debug(f'{websocket.id} disconnected')


async def main(host: str, port: int, token: str,
               config) -> None:
    global TOKEN
    TOKEN = token
    log.debug(f'Serving on ws://{host}:{port}')
    dsn = config.applications[0].configuration['dsn']
    session_manager = SessionManager(dsn, Base, session_config={
        'autoflush': False})
    async with serve(handle_start, host, port,
                     create_protocol=partial(WebSocketServer, config,
                                             session_manager)):
        await Future()
