import hashlib
import http
from asyncio import Future
from functools import cached_property, partial
from http.cookies import SimpleCookie
from json import dumps, loads
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

import transaction
from itsdangerous import BadSignature, Signer
from markupsafe import escape
from websockets.exceptions import ConnectionClosed, InvalidOrigin
from websockets.legacy.protocol import broadcast
from websockets.legacy.server import WebSocketServerProtocol, serve

from onegov.chat.collections import ChatCollection
from onegov.chat.utils import param_from_path
from onegov.core import cache
from onegov.core.browser_session import BrowserSession
from onegov.core.orm import Base, SessionManager
from onegov.user import User, UserCollection
from onegov.websockets import log
from onegov.websockets.security import (WebsocketSecurityError,
                                        consume_websocket_token)

if TYPE_CHECKING:
    from collections.abc import Collection
    from uuid import UUID

    from sqlalchemy.orm import Session
    from websockets import Headers
    from websockets.legacy.server import HTTPResponse

    from onegov.chat.models import Chat
    from onegov.core.types import JSONObject, JSONObject_ro
    from onegov.server.config import Config


CONNECTIONS: dict[str, set[WebSocketServerProtocol]] = {}
TOKEN = ''  # nosec: B105

NOTFOUND = object()
SESSIONS: dict[str, 'Session'] = {}
STAFF_CONNECTIONS: dict[str, set[WebSocketServerProtocol]] = {}
STAFF: dict[str, dict[str, User]] = {}  # For Authentication of User
ACTIVE_CHATS: dict[str, dict['UUID', 'Chat']] = {}  # For DB
CHANNELS: dict[str, dict[str, set[WebSocketServerProtocol]]] = {}


class WebSocketServer(WebSocketServerProtocol):
    """ A websocket server connection.

    This protocol handles multiple websocket applications:
    - Ticket notifications
    - Ticker
    - Chat

    Chat behaves differently from the others and will eventually be carved out
    into a separate service. To not interfere with any existing functionality,
    we try to refrain from making backwards-incompatible changes.  That way,
    ticker and notifications should continue to work without any modification.

    TODO: Move chat to a dedicated service.
    """
    schema: str
    user_id: str | None
    signed_session_id: str | None

    def __init__(
        self,
        config: 'Config',
        session_manager: SessionManager,
        *args: Any,
        **kwargs: Any
    ):
        super().__init__(*args, **kwargs)
        self.config = config
        self.session_manager = session_manager

    async def process_request(
        self,
        path: str,
        headers: 'Headers'
    ) -> 'HTTPResponse | None':
        """ Intercept initial HTTP request.

        Before establishing a WebSocket connection, a client sends a HTTP
        request to "upgrade" the connection to a WebSocket connection.

        Chat
        ----
        We authenticate the user before creating the WebSocket connection. The
        user is identified based on the session cookie. In addition to the
        cookie, we require a one-time token that the user must have obtained
        prior to requesting the WebSocket connection.
        """
        url = urlparse(path)

        if '/chats' not in url.path:
            # For non-chat requests (e.g., ticker) we'll skip the dance below
            # and let the protocol handle authentication
            # (handle_authentication).
            return None

        try:
            cookie = SimpleCookie(headers['Cookie'])
            session_id = cookie['session_id'].value
        except KeyError:
            log.error(
                "No session cookie found in request. "
                "Check that you sent the request from the same origin as "
                f"the WebSocket server ({self.host})"
            )

            return http.HTTPStatus.BAD_REQUEST, [], b""

        self.signed_session_id = session_id

        try:
            self.schema = param_from_path('schema', path)
        except ValueError as err:
            log.error(
                f"Unable to retrieve schema from path: {path}",
                exc_info=err
            )
            return http.HTTPStatus.BAD_REQUEST, [], b""

        # browser_session requires self.schema
        self.user_id = self.browser_session.get("userid")

        try:
            # Consume the presented token or deny the connection. The token
            # acts like CSRF token to protect against Cross-Site WebSocket
            # Hijacks.
            consume_websocket_token(path, self.browser_session)
        except WebsocketSecurityError as err:
            log.error("Rejecting WebSocket connection.", exc_info=err)
            return http.HTTPStatus.UNAUTHORIZED, [], b""

        try:
            # Checking the origin is done at a later stage by handshake(), this
            # check is totally superfluous. However, rejecting clients because
            # of a wrong origin would get unnoticed otherwise. You can safely
            # delete this block in the future.
            #
            # TODO: Pass in valid origins. Is there already a list of allowed
            # origins?
            self.process_origin(headers, self.origins)
        except InvalidOrigin as err:
            log.debug("WebSocket connection will be rejected.", exc_info=err)

        self.populate_staff()

        return None

    def populate_staff(self) -> None:
        """
        Populate staff users.
        """
        STAFF[self.schema] = {
            user.username: user for user in
            (
                UserCollection(self.session)
                .query()
                .filter(User.role.in_(['editor', 'admin']))
            )
        }

        transaction.commit()

    async def get_chat(self, id: 'UUID') -> 'Chat':
        chat = ACTIVE_CHATS.setdefault(self.schema, {}).get(id, NOTFOUND)

        # Force (cached) session to fetch latest state of the database,
        # otherwise new chats are not visible to this session.
        self.session.expire_all()
        transaction.commit()

        if chat is NOTFOUND:
            chat = ChatCollection(self.session).by_id(id)

            log.debug(f'searching for chat with id {id}')
            log.debug(f'chat from collection {chat}')

            if chat and not chat.active:
                chat = None

            ACTIVE_CHATS[self.schema][id] = chat  # type: ignore

        transaction.commit()
        return chat  # type: ignore

    async def update_database(self) -> None:
        self.session.flush()
        transaction.commit()

    def unsign(self, text: str) -> str | None:
        """ Unsigns a signed text, returning None if unsuccessful. """
        identity_secret = self.application_config[
            'identity_secret'] + self.application_id_hash
        try:
            signer = Signer(identity_secret, salt='generic-signer')
            return signer.unsign(text).decode('utf-8')
        except BadSignature:
            return None

    @property
    def session(self) -> 'Session':
        self.session_manager.set_current_schema(self.schema)

        session = self.session_manager.session()

        ACTIVE_CHATS[self.schema] = {}

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
    def namespace(self) -> str:
        return self.schema.split('-', 1)[0]

    @property
    def application_id(self) -> str:
        return '/'.join(self.schema.split('-', 1))

    @property
    def application_config(self) -> dict[str, Any]:
        for c in self.config.applications:
            if c.namespace == self.namespace:
                return c.configuration

        return {}

    @cached_property
    def browser_session(self) -> 'BrowserSession | dict[str, Any]':
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


async def handle_customer_chat(
    websocket: WebSocketServer,
    payload: 'JSONObject_ro'
) -> None:
    """
    Starts a chat. Handles listening to messages on channel.
    """

    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return

    if "active_chat_id" not in websocket.browser_session:
        log.error(
            "Unable to find active_chat_id in session, aborting."
        )
        return None

    channel = websocket.browser_session["active_chat_id"]

    await acknowledge(websocket)

    all_channels = CHANNELS.setdefault(schema, {})

    channel_connections = all_channels.setdefault(
        channel.hex,
        set()
    )

    channel_connections.add(websocket)
    staff_connections = STAFF_CONNECTIONS.setdefault(schema, set())

    chat = await websocket.get_chat(channel.hex)

    log.debug(f'added {websocket.id} to channel-connections')

    while websocket.open:
        try:
            message = await websocket.recv()
            log.debug(f'customer {websocket.id!r} got the message {message!r}')

            if loads(message)['type'] == 'message':
                stored = ChatCollection(websocket.session).by_id(channel)

                if not stored:
                    log.error(f"Unable to find stored chat with {channel=}")
                    continue

                chat = stored
                content = loads(message)

                closed_connections = []

                for client in channel_connections:

                    try:
                        await client.send(dumps({
                            'type': "notification",
                            'message': message,
                        }))
                    except ConnectionClosed as err:
                        log.error(
                            "Attempting to communicate with a closed"
                            "connection, removing client from channels.",
                            exc_info=err
                        )

                        closed_connections.append(client)

                for connection in closed_connections:
                    channel_connections.remove(connection)

                # If customer is the only connection send chat request
                if len(channel_connections) == 1 and not chat.user_id:
                    log.debug('only client in channel, sending request.')
                    for client in staff_connections:
                        await client.send(dumps({
                            'type': "notification",
                            'message': dumps({
                                'type': 'request',
                                'text': content['text'],
                                'userId': content['userId'],
                                'user': content['user'],
                                'topic': chat.topic,
                                'channel': channel.hex
                            })
                        }))

                chat_history = chat.chat_history.copy()

                chat_history.append({  # type: ignore
                    'userId': escape(content['userId']),
                    'user': escape(content['user']),
                    'text': escape(content['text']),
                    'time': escape(content['time']),
                })
                chat.chat_history = chat_history

        except Exception as e:
            log.exception("The debugged error message is -", exc_info=e)
            channel_connections.remove(websocket)
            log.debug(f'removed {websocket.id} from channel-connections')
        finally:
            await websocket.update_database()

    return None


async def handle_staff_chat(
    websocket: WebSocketServer,
    payload: 'JSONObject_ro'
) -> None:
    """
    Registers staff member and listens to messages.
    """

    schema = payload.get('schema')
    if not schema or not isinstance(schema, str):
        await error(websocket, f'invalid schema: {schema}')
        return

    websocket.session
    await acknowledge(websocket)

    if websocket.user_id in STAFF[schema]:
        log.debug('User is in Database.')

        all_channels = CHANNELS.setdefault(schema, {})
        staff_connections = STAFF_CONNECTIONS.setdefault(schema, set())
        staff_connections.add(websocket)
        channel_connections: set[WebSocketServerProtocol] = set()
        open_channel = ''

        log.debug(f'added {websocket.id} to staff-connections')

        while websocket.open:
            try:
                message = await websocket.recv()
                content = loads(message)
                log.debug(
                    f'staff member {websocket.id!r} '
                    f'got the message {message!r}'
                )

                # Forward each websocket message, no matter the type
                log.debug(
                    f'current channel connections: {channel_connections}')

                closed_connections = []

                for client in channel_connections:

                    try:
                        await client.send(dumps({
                            'type': "notification",
                            'message': message,
                        }))
                    except ConnectionClosed as err:
                        log.error(
                            "Attempting to communicate with a closed"
                            "connection, removing client from channels.",
                            exc_info=err
                        )

                        closed_connections.append(client)

                for connection in closed_connections:
                    channel_connections.remove(connection)

                # If the type is a message, save to DB
                if content['type'] == 'message':

                    chat = (
                        ChatCollection(websocket.session)
                        .by_id(open_channel)
                    )

                    if not chat:
                        log.error(
                            f"Unable to find stored chat with {open_channel=}"
                        )
                        continue

                    log.debug(f'staff received message {content}')

                    chat_history = chat.chat_history.copy()
                    chat_history.append({  # type: ignore
                        'userId': escape(content['userId']),
                        'user': escape(content['user']),
                        'text': escape(content['text']),
                        'time': escape(content['time']),
                    })
                    chat.chat_history = chat_history

                elif content['type'] == 'reconnect':
                    log.debug(f'reconnecting to channel {content["channel"]}')
                    channel_connections = all_channels.setdefault(
                        content["channel"], set()
                    )
                    channel_connections.add(websocket)

                elif content['type'] == 'end-chat':
                    log.debug(f'ending chat with id {content["channel"]}')
                    chat = ChatCollection(websocket.session).by_id(
                        escape(content['channel'])
                    )

                    if not chat:
                        log.error(
                            "Unable to find stored chat"
                            f"with {content['channel']=}"
                        )

                        continue

                    chat.active = False

                elif content['type'] == 'accepted':
                    log.debug('staff-member accepted-request')
                    open_channel = loads(message)['channel']
                    channel_connections = all_channels.setdefault(
                        open_channel, set()
                    )
                    channel_connections.add(websocket)

                    chat = ChatCollection(websocket.session).by_id(
                        open_channel)
                    if not chat:
                        log.error(
                            "Unable to find stored chat"
                            f"with {open_channel=}"
                        )
                        continue

                    # Tell everone else you've accepted
                    for client in staff_connections:
                        if client != websocket:
                            inner = dumps({
                                'type': 'hide-request',
                                'channel': open_channel
                            })
                            await client.send(dumps({
                                'type': "notification",
                                'message': inner,
                            }))

                    inner = dumps({
                        'type': 'chat-history',
                        'history': chat.chat_history,
                        'channel': open_channel
                    })
                    await websocket.send(dumps({
                        'type': "notification",
                        'message': inner,
                    }))
                    log.debug('sent chat history')

                    chat.user_id = escape(content['userId'])

                elif content['type'] == 'request-chat-history':
                    open_channel = content['channel']
                    chat = ChatCollection(websocket.session).by_id(
                        open_channel)

                    if not chat:
                        log.error(
                            "Unable to find stored chat"
                            f"with {open_channel=}"
                        )

                        continue

                    channel_connections = all_channels.setdefault(open_channel,
                                                                  set())
                    channel_connections.add(websocket)
                    log.debug('staff member reconnected')
                    inner = dumps({
                        'type': 'chat-history',
                        'history': chat.chat_history,
                        'channel': open_channel
                    })
                    await websocket.send(dumps({
                        'type': "notification",
                        'message': inner,
                    }))

            except Exception as e:
                log.exception("The debugged error message is -", exc_info=e)
                if websocket in staff_connections:
                    staff_connections.remove(websocket)
                log.debug(f'removed {websocket.id} from staff-connections')
            finally:
                await websocket.update_database()


async def handle_start(websocket: WebSocketServerProtocol) -> None:
    log.debug(f'{websocket.id} connected')
    message = await websocket.recv()
    payload = get_payload(message, ('authenticate', 'register',
                                    'customer_chat', 'staff_chat'))
    if payload and payload['type'] == 'authenticate':
        await handle_manage(websocket, payload)
    elif payload and payload['type'] == 'register':
        await handle_listen(websocket, payload)
    elif payload and (payload['type'] == 'customer_chat'):
        await handle_customer_chat(websocket, payload)  # type: ignore
    elif payload and (payload['type'] == 'staff_chat'):
        await handle_staff_chat(websocket, payload)  # type: ignore
    else:
        # FIXME: technically message can be bytes
        await error(websocket, f'invalid command: {message}')  # type:ignore
    log.debug(f'{websocket.id} disconnected')


async def main(
    host: str, port: int, token: str,
    config: 'Config | None' = None
) -> None:

    global TOKEN
    TOKEN = token
    log.debug(f'Serving on ws://{host}:{port}')

    if config:
        dsn = config.applications[0].configuration['dsn']

        session_manager = SessionManager(
            dsn,
            Base,
            session_config={'autoflush': False}
        )

        async with serve(handle_start, host, port,
                         create_protocol=partial(WebSocketServer, config,
                                                 session_manager)):
            await Future()

    else:
        async with serve(handle_start, host, port):
            await Future()
