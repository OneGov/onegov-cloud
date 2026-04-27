from __future__ import annotations

import pytest
import time
import transaction

from datetime import timedelta
from onegov.core import Framework
from onegov.core.security.identity_policy import IdentityPolicy
from onegov.core.utils import Bunch
from onegov.user import Auth, User, UserCollection, UserApp
from onegov.user.errors import AccountLockedError
from onegov.user.errors import ExpiredSignupLinkError
from onegov.user.errors import RateLimitError
from sedate import utcnow
from unittest.mock import patch
from webtest import TestApp as Client
from yubico_client import Yubico  # type: ignore[import-untyped]


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.request import CoreRequest
    from sqlalchemy.orm import Session
    from tests.shared.capturelog import CaptureLogFixture
    from webob import Response


class DummyApp:

    sent_sms: list[tuple[str, str]]
    can_deliver_sms = True

    def __init__(
        self,
        session: Session,
        application_id: str = 'my-app'
    ) -> None:

        self._session = session
        self.application_id = application_id
        self.sent_sms = []

    def session(self) -> Session:
        return self._session

    def send_sms(self, number: str, content: str) -> None:
        self.sent_sms.append((number, content))


def test_auth_login(session: Session) -> None:
    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    session.expire_all()
    auth = Auth(DummyApp(session))  # type: ignore[arg-type]

    request: Any = None
    assert not auth.authenticate(
        request=request, username='AzureDiamond', password='hunter1')
    assert not auth.authenticate(
        request=request, username='AzureDiamonb', password='hunter2')
    user = auth.authenticate(
        request=request, username='AzureDiamond', password='hunter2')

    assert isinstance(user, User)
    identity = auth.as_identity(user)
    assert identity.userid == 'azurediamond'
    assert identity.role == 'irc-user'
    assert identity.application_id == 'my-app'


def test_auth_login_inactive(session: Session) -> None:
    user = UserCollection(session).add(
        'AzureDiamond', 'hunter2', 'irc-user', active=False)

    auth = Auth(DummyApp(session))  # type: ignore[arg-type]

    request: Any = None
    assert not auth.authenticate(
        request=request, username='AzureDiamond', password='hunter2')

    user.active = True
    transaction.commit()

    assert auth.authenticate(
        request=request, username='AzureDiamond', password='hunter2')


def test_auth_login_yubikey(session: Session) -> None:
    UserCollection(session).add(
        username='admin@example.org',
        password='p@ssw0rd',
        role='admin',
        second_factor={
            'type': 'yubikey',
            'data': 'ccccccbcgujh'
        }
    )

    app = DummyApp(session)
    app.yubikey_client_id = 'abc'  # type: ignore[attr-defined]
    app.yubikey_secret_key = 'dGhlIHdvcmxkIGlzIGNvbnRyb2xsZWQgYnkgbGl6YXJkcyE='  # type: ignore[attr-defined]

    auth = Auth(app)  # type: ignore[arg-type]

    request: Any = None
    assert not auth.authenticate(
        request=request, username='admin@example.org', password='p@ssw0rd')
    assert not auth.authenticate(
        request=request,
        username='admin@example.org',
        password='p@ssw0rd',
        second_factor='xxxxxxbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = False

        assert not auth.authenticate(
            request=request,
            username='admin@example.org',
            password='p@ssw0rd',
            second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )

    with patch.object(Yubico, 'verify') as verify:
        verify.return_value = True

        user = auth.authenticate(
            request=request,
            username='admin@example.org',
            password='p@ssw0rd',
            second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
        )

    assert isinstance(user, User)
    identity = auth.as_identity(user)
    assert identity.userid == 'admin@example.org'
    assert identity.role == 'admin'
    assert identity.application_id == 'my-app'


def test_auth_login_unnecessary_yubikey(session: Session) -> None:
    UserCollection(session).add(
        username='admin@example.org',
        password='p@ssw0rd',
        role='admin'
    )

    auth = Auth(DummyApp(session))  # type: ignore[arg-type]

    # simply ignore the second factor
    assert auth.authenticate(
        request=None,  # type: ignore[arg-type]
        username='admin@example.org',
        password='p@ssw0rd',
        second_factor='ccccccbcgujhingjrdejhgfnuetrgigvejhhgbkugded'
    )


def test_auth_logging(capturelog: CaptureLogFixture, session: Session) -> None:
    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    auth = Auth(DummyApp(session))  # type: ignore[arg-type]
    request: Any = None

    # XXX do not change the following messages, as they are used that way in
    # fail2ban already and should remain exactly the same
    capturelog.handler.records.clear()
    auth.authenticate(
        request=request, username='AzureDiamond', password='hunter1')
    assert capturelog.records()[0].message == (
        "Failed login by unknown (AzureDiamond)")

    capturelog.handler.records.clear()
    auth.authenticate(
        request=request, username='AzureDiamond', password='hunter1',
        client='127.0.0.1')
    assert capturelog.records()[0].message == (
        "Failed login by 127.0.0.1 (AzureDiamond)")

    capturelog.handler.records.clear()
    auth.authenticate(
        request=request, username='AzureDiamond', password='hunter2',
        client='127.0.0.1')
    assert capturelog.records()[0].message == (
        "Successful login by 127.0.0.1 (AzureDiamond)")


def test_auth_integration(session: Session, redis_url: str) -> None:

    class App(Framework, UserApp):
        pass

    @App.identity_policy()
    def get_identity_policy() -> IdentityPolicy:
        return IdentityPolicy()

    @App.path(path='/auth', model=Auth)
    def get_auth() -> Auth:
        return Auth(DummyApp(session), to='https://abc.xyz/go')  # type: ignore[arg-type]

    @App.view(model=Auth)
    def view_auth(self: Auth, request: CoreRequest) -> Response | str:
        return self.login_to(
            request.GET['username'],
            request.GET['password'],
            request
        ) or 'Error'

    @App.view(model=Auth, name='logout')
    def view_logout(self: Auth, request: CoreRequest) -> Response:
        return self.logout_to(request)

    App.commit()

    UserCollection(session).add('AzureDiamond', 'hunter2', 'irc-user')
    transaction.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(
        identity_secure=False,
        redis_url=redis_url
    )
    app.application_id = 'test/foo'

    client = Client(app)

    response = client.get('/auth?username=AzureDiamond&password=hunter1')
    assert response.text == 'Error'
    user = UserCollection(session).by_username('AzureDiamond')
    assert user is not None
    assert not user.sessions

    response = client.get('/auth?username=AzureDiamond&password=hunter2')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'
    assert response.headers['Set-Cookie'].startswith('session_id')
    session_id = app.unsign(response.request.cookies['session_id'])
    user = UserCollection(session).by_username('AzureDiamond')
    assert user is not None
    assert user.sessions
    assert session_id in user.sessions

    response = client.get('/auth/logout')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'

    user = UserCollection(session).by_username('AzureDiamond')
    assert user is not None
    assert not user.sessions

    response = client.get('/auth?username=AzureDiamond&password=hunter2')
    assert response.status_code == 302
    assert response.location == 'http://localhost/go'
    assert response.headers['Set-Cookie'].startswith('session_id')
    new_session_id = app.unsign(response.request.cookies['session_id'])
    assert new_session_id != session_id
    user = UserCollection(session).by_username('AzureDiamond')
    assert user is not None
    assert user.sessions
    assert new_session_id in user.sessions


def test_signup_token_data(session: Session) -> None:
    auth = Auth(DummyApp(session, 'foo'), signup_token_secret='bar')  # type: ignore[arg-type]
    assert auth.new_signup_token('admin')

    token = auth.new_signup_token('admin', max_age=1)
    data = auth.decode_signup_token(token)
    assert data is not None
    assert data['role'] == 'admin'
    assert data['max_uses'] == 1

    now = utcnow().replace(tzinfo=None)
    before = int((now - timedelta(seconds=1)).timestamp())
    after = int((now + timedelta(seconds=1)).timestamp())
    assert before <= data['expires'] <= after


def test_signup_max_uses(session: Session) -> None:
    auth = Auth(DummyApp(session, 'foo'), signup_token_secret='bar')  # type: ignore[arg-type]
    auth.signup_token = auth.new_signup_token('admin', max_age=10, max_uses=1)

    foo = auth.register(
        form=Bunch(  # type: ignore[arg-type]
            username=Bunch(data='foo@example.org'),
            password=Bunch(data='correct horse'),
        ),
        request=Bunch(  # type: ignore[arg-type]
            client_addr='127.0.0.1'
        )
    )

    assert foo.role == 'admin'

    with pytest.raises(ExpiredSignupLinkError):
        auth.register(
            form=Bunch(  # type: ignore[arg-type]
                username=Bunch(data='bar@example.org'),
                password=Bunch(data='battery staple'),
            ),
            request=Bunch(  # type: ignore[arg-type]
                client_addr='127.0.0.1'
            )
        )


def test_signup_expired(session: Session) -> None:
    auth = Auth(DummyApp(session, 'foo'), signup_token_secret='bar')  # type: ignore[arg-type]
    auth.signup_token = auth.new_signup_token('admin', max_age=1, max_uses=2)

    foo = auth.register(
        form=Bunch(  # type: ignore[arg-type]
            username=Bunch(data='foo@example.org'),
            password=Bunch(data='correct horse'),
        ),
        request=Bunch(  # type: ignore[arg-type]
            client_addr='127.0.0.1'
        )
    )

    assert foo.role == 'admin'

    time.sleep(2)

    with pytest.raises(ExpiredSignupLinkError):
        auth.register(
            form=Bunch(  # type: ignore[arg-type]
                username=Bunch(data='bar@example.org'),
                password=Bunch(data='battery staple'),
            ),
            request=Bunch(  # type: ignore[arg-type]
                client_addr='127.0.0.1'
            )
        )


def test_last_login_timestamp(session: Session, redis_url: str) -> None:

    class App(Framework, UserApp):
        pass

    @App.identity_policy()
    def get_identity_policy() -> IdentityPolicy:
        return IdentityPolicy()

    @App.path(path='/auth', model=Auth)
    def get_auth() -> Auth:
        return Auth(DummyApp(session), to='/')  # type: ignore[arg-type]

    @App.view(model=Auth)
    def view_auth(self: Auth, request: CoreRequest) -> Response | str:
        return (
            self.login_to(
                request.GET['username'], request.GET['password'], request
            )
            or 'Error'
        )

    App.commit()

    UserCollection(session).add('testuser', 'testpass', 'member')
    transaction.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(identity_secure=False, redis_url=redis_url)
    app.application_id = 'test/last-login'

    client = Client(app)

    user = UserCollection(session).by_username('testuser')
    assert user is not None
    assert user.last_login is None

    before_login = utcnow()
    response = client.get('/auth?username=testuser&password=testpass')
    after_login = utcnow()

    assert response.status_code == 302

    session.expire_all()
    user = UserCollection(session).by_username('testuser')
    assert user is not None
    assert user.last_login is not None
    assert before_login <= user.last_login <= after_login

    first_login = user.last_login
    time.sleep(0.1)

    response = client.get('/auth?username=testuser&password=testpass')
    assert response.status_code == 302

    session.expire_all()
    user = UserCollection(session).by_username('testuser')
    assert user is not None
    assert user.last_login is not None
    assert user.last_login > first_login


def _make_rate_limit_app(
    postgres_dsn: str,
    redis_url: str,
    app_id: str,
    ip_requests: int = 1000,
    ip_expiration: int = 300,
    account_attempts: int = 1000,
    account_lockout: int = 300,
) -> tuple[Any, Any]:
    """Return a configured (Framework+UserApp, session) pair.

    The app owns its session so all reads/writes share one connection.
    Each test uses a unique app_id to namespace the Redis rate-limit cache.
    """

    class App(Framework, UserApp):
        pass

    @App.identity_policy()
    def get_identity_policy() -> IdentityPolicy:
        return IdentityPolicy()

    App.commit()

    app = App()
    app.namespace = 'test'
    app.configure_application(
        dsn=postgres_dsn,
        identity_secure=False,
        redis_url=redis_url,
        login_rate_limit={
            'ip_requests': ip_requests,
            'ip_expiration': ip_expiration,
            'account_attempts': account_attempts,
            'account_lockout': account_lockout,
        },
    )
    app.set_application_id(app_id)
    return app, app.session()


def test_ip_rate_limit(postgres_dsn: str, redis_url: str) -> None:
    app, session = _make_rate_limit_app(
        postgres_dsn, redis_url,
        app_id='test/ip-rate-limit',
        ip_requests=2,
        ip_expiration=300,
        account_attempts=1000,
    )
    UserCollection(session).add('alice@example.org', 'correct', 'member')
    transaction.commit()

    auth = Auth(app)
    request: Any = None

    # two wrong-password attempts
    assert auth.authenticate(
        request=request, username='alice@example.org',
        password='wrong', client='1.2.3.4') is None
    assert auth.authenticate(
        request=request, username='alice@example.org',
        password='wrong', client='1.2.3.4') is None

    # third attempt from same IP hits the limit
    with pytest.raises(RateLimitError):
        auth.authenticate(
            request=request, username='alice@example.org',
            password='wrong', client='1.2.3.4')

    # correct password is also blocked while the IP is rate-limited
    with pytest.raises(RateLimitError):
        auth.authenticate(
            request=request, username='alice@example.org',
            password='correct', client='1.2.3.4')

    # a different IP is unaffected
    assert auth.authenticate(
        request=request, username='alice@example.org',
        password='correct', client='9.9.9.9') is not None


def test_account_lockout(postgres_dsn: str, redis_url: str) -> None:
    app, session = _make_rate_limit_app(
        postgres_dsn, redis_url,
        app_id='test/account-lockout',
        ip_requests=1000,
        account_attempts=3,
        account_lockout=900,  # 15 min → minutes_remaining should be 15
    )
    UserCollection(session).add('bob@example.org', 'correct', 'member')
    transaction.commit()

    auth = Auth(app)
    request: Any = None

    # three wrong-password attempts
    for _ in range(3):
        assert auth.authenticate(
            request=request, username='bob@example.org',
            password='wrong', client='1.2.3.4') is None

    # fourth attempt locks account
    with pytest.raises(AccountLockedError) as exc_info:
        auth.authenticate(
            request=request, username='bob@example.org',
            password='wrong', client='1.2.3.4')
    assert exc_info.value.minutes_remaining == 15

    # correct password is also rejected
    with pytest.raises(AccountLockedError):
        auth.authenticate(
            request=request, username='bob@example.org',
            password='correct', client='1.2.3.4')


def test_account_lockout_resets_on_success(
    postgres_dsn: str, redis_url: str
) -> None:
    app, session = _make_rate_limit_app(
        postgres_dsn, redis_url,
        app_id='test/lockout-reset',
        ip_requests=1000,
        account_attempts=3,
        account_lockout=900,
    )
    UserCollection(session).add('carol@example.org', 'correct', 'member')
    transaction.commit()

    auth = Auth(app)
    request: Any = None

    # two failed attempts — not yet locked
    for _ in range(2):
        auth.authenticate(
            request=request, username='carol@example.org',
            password='wrong', client='1.2.3.4')
        transaction.commit()

    user = UserCollection(session).by_username('carol@example.org')
    assert user is not None
    assert user.failed_login_attempts == 2

    # successful login clears the counters
    assert auth.authenticate(
        request=request, username='carol@example.org',
        password='correct', client='1.2.3.4') is not None
    transaction.commit()

    user = UserCollection(session).by_username('carol@example.org')
    assert user is not None
    assert not user.failed_login_attempts


def test_account_lockout_expires(postgres_dsn: str, redis_url: str) -> None:
    app, session = _make_rate_limit_app(
        postgres_dsn, redis_url,
        app_id='test/lockout-expires',
        ip_requests=1000,
        account_attempts=3,
        account_lockout=300,
    )
    user = UserCollection(session).add('dan@example.org', 'correct', 'member')
    # simulate 3 failed attempts from 301 seconds ago
    user.failed_login_attempts = 3
    user.failed_login_at = (
        utcnow().replace(tzinfo=None) - timedelta(seconds=301)
    ).isoformat()
    transaction.commit()

    auth = Auth(app)
    request: Any = None

    # lockout has expired — correct password works again
    result = auth.authenticate(
        request=request, username='dan@example.org',
        password='correct', client='1.2.3.4')
    assert result is not None
    transaction.commit()

    user = UserCollection(session).by_username('dan@example.org')
    assert user is not None
    assert not user.failed_login_attempts
