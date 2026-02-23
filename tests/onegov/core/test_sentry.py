from __future__ import annotations

import pytest
import sentry_sdk
from morepath import Identity
from onegov.core.framework import Framework
from onegov.core.security import Public
from onegov.core.sentry import OneGovCloudIntegration
from sentry_sdk import capture_message, add_breadcrumb
from sentry_sdk.transport import Transport
from sqlalchemy.exc import InterfaceError
from tests.shared import Client
from tests.shared.utils import create_app
from unittest.mock import Mock
from webob import Response
from webob.exc import HTTPOk


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from onegov.core.request import CoreRequest
    from sentry_sdk.client import BaseClient
    from sentry_sdk.envelope import Envelope
    from sentry_sdk.types import Event, Hint

# NOTE: The following test fixtures are copied over from sentry-sdk
#       but they have been simplified slightly, we may wish to validate
#       the json schema for the event, like sentry does it


@pytest.fixture
def monkeypatch_test_transport(
    monkeypatch: pytest.MonkeyPatch
) -> Callable[[BaseClient], None]:
    def inner(client: BaseClient) -> None:
        monkeypatch.setattr(client, 'transport', MyTestTransport())

    return inner


class MyTestTransport(Transport):
    def __init__(self) -> None:
        Transport.__init__(self)
        self.capture_event = lambda event: None  # type: ignore[method-assign]
        self._queue = None

    def capture_envelope(self, envelope: object) -> None:
        pass


@pytest.fixture
def sentry_init(
    monkeypatch_test_transport: Callable[[BaseClient], None],
    request: pytest.FixtureRequest
) -> Iterator[Callable[..., None]]:

    def inner(*a: Any, **kw: Any) -> None:
        client = sentry_sdk.Client(*a, **kw)
        sentry_sdk.get_global_scope().set_client(client)
        if 'transport' not in kw:
            monkeypatch_test_transport(sentry_sdk.get_client())

    if request.node.get_closest_marker('forked'):
        # Do not run isolation if the test is already running in
        # ultimate isolation (seems to be required for celery tests that
        # fork)
        yield inner
    else:
        with sentry_sdk.scope.use_isolation_scope(None):  # type: ignore[arg-type]
            yield inner


@pytest.fixture
def capture_events(
    monkeypatch: pytest.MonkeyPatch
) -> Callable[[], list[Event]]:

    def inner() -> list[Event]:
        events = []
        test_client = sentry_sdk.get_client()
        assert test_client.transport is not None
        old_capture_event = test_client.transport.capture_event
        old_capture_envelope = test_client.transport.capture_envelope

        def append_event(event: Event) -> str | None:
            events.append(event)
            return old_capture_event(event)

        def append_envelope(envelope: Envelope) -> str | None:
            for item in envelope:
                if item.headers.get('type') in ('event', 'transaction'):
                    assert test_client.transport is not None
                    test_client.transport.capture_event(item.payload.json)  # type: ignore[arg-type]
            return old_capture_envelope(envelope)

        monkeypatch.setattr(
            test_client.transport, 'capture_event', append_event)
        monkeypatch.setattr(
            test_client.transport, 'capture_envelope', append_envelope)
        return events

    return inner


@pytest.fixture
def capture_exceptions(
    monkeypatch: pytest.MonkeyPatch
) -> Callable[[], set[Exception]]:

    def inner() -> set[Exception]:
        errors = set()
        old_capture_event = sentry_sdk.capture_event

        def capture_event(
            event: Event,
            hint: Hint | None = None
        ) -> str | None:
            if hint:
                if 'exc_info' in hint:
                    error = hint['exc_info'][1]
                    errors.add(error)
            return old_capture_event(event, hint=hint)

        monkeypatch.setattr(sentry_sdk, 'capture_event', capture_event)
        return errors

    return inner


@pytest.fixture
def mock_view() -> Mock:
    # this way we can set a side effect on the view
    return Mock(return_value=Response())


@pytest.fixture
def sentry_app(
    sentry_init: Callable[..., Any],
    request: pytest.FixtureRequest,
    mock_view: Mock
) -> Framework:

    class TestModel:
        pass

    # we create a new app class so any paths/views we
    # register won't leak to the rest of the tests
    class MyApp(Framework):
        pass

    # create some test routes/views
    @MyApp.path(model=TestModel, path='/test')
    def test_path(app: MyApp) -> TestModel:
        return TestModel()

    @MyApp.view(model=TestModel, permission=Public)
    def test_view(self: TestModel, request: CoreRequest) -> Response:
        add_breadcrumb({'message': 'test_view'})
        return mock_view(self, request)

    # we need to sentry_init before creating the app class
    # since OneGovCloudIntegration registers a tween
    with_ppi = getattr(request, 'param', False)
    sentry_init(
        # we allow ourselves to optionally parametrize whether
        # or not to send personally identifiable information
        send_default_pii=with_ppi,
        integrations=[OneGovCloudIntegration()]
    )

    app = create_app(
        MyApp,
        request
    )
    app.with_ppi = with_ppi  # type: ignore[attr-defined]
    return app


@pytest.fixture
def sentry_client(sentry_app: Framework) -> Client:
    client = Client(sentry_app)
    client.with_ppi = sentry_app.with_ppi  # type: ignore[attr-defined]
    return client


def test_view_exceptions(
    mock_view: Mock,
    sentry_client: Client,
    capture_events: Callable[[], list[Event]],
    capture_exceptions: Callable[[], set[Exception]]
) -> None:

    events = capture_events()
    exceptions = capture_exceptions()

    # this breadcrumb should get cleared by the wsgi scope
    old_breadcrumb = {'message': 'test'}
    add_breadcrumb(old_breadcrumb)

    mock_view.side_effect = ZeroDivisionError
    with pytest.raises(ZeroDivisionError):
        sentry_client.get('/test')

    (error,) = exceptions
    assert isinstance(error, ZeroDivisionError)

    (event,) = events
    assert old_breadcrumb not in event['breadcrumbs']['values']  # type: ignore[index]
    # FIXME: redis appears to insert a breadcrumb whether or not we
    #        activated the redis integration, so we get more than one
    #        breadcrumb here, we should figure out why that is
    assert any(
        breadcrumb['message'] == 'test_view'
        for breadcrumb in event['breadcrumbs']['values']  # type: ignore[index]
    )

    last_exception = event['exception']['values'][-1]
    assert last_exception['mechanism']['type'] == 'onegov-cloud'
    assert last_exception['type'] == 'ZeroDivisionError'


def test_view_http_exception(
    mock_view: Mock,
    sentry_client: Client,
    capture_events: Callable[[], list[Event]],
    capture_exceptions: Callable[[], set[Exception]]
) -> None:

    events = capture_events()
    exceptions = capture_exceptions()

    # a http exception should not raise
    # we use HTTPOk, so we don't have to ignore the
    # WebTest error on non-200 responses
    mock_view.side_effect = HTTPOk
    sentry_client.get('/test')

    # it should also not be recorded by sentry
    assert not exceptions

    # no exceptions means no events either
    assert not events


def test_view_db_connection_exception(
    mock_view: Mock,
    sentry_client: Client,
    capture_events: Callable[[], list[Event]],
    capture_exceptions: Callable[[], set[Exception]]
) -> None:

    events = capture_events()
    exceptions = capture_exceptions()

    # a db connection error should not raise, but it will
    # cause a 500 response
    mock_view.side_effect = InterfaceError('', '', Exception())
    sentry_client.get('/test', expect_errors=True)

    # it should also not be recorded by sentry
    assert not exceptions

    # no exceptions means no events either
    assert not events


@pytest.mark.parametrize('sentry_app', [
    pytest.param(True, id='with ppi'),
    pytest.param(False, id='without ppi'),
], indirect=['sentry_app'])
def test_has_context(
    mock_view: Mock,
    sentry_app: Framework,
    sentry_client: Client,
    capture_events: Callable[[], list[Event]]
) -> None:

    events = capture_events()

    def view(self: object, request: CoreRequest) -> Response:
        capture_message('test_message')
        return Response()

    mock_view.side_effect = view

    sentry_client.get('/test')

    (event,) = events
    assert event['message'] == 'test_message'
    assert event['request']['url'] == 'http://localhost/test'
    if sentry_app.with_ppi:  # type: ignore[attr-defined]
        assert event['user'] == {
            'id': None,
            'data': {'role': 'anonymous'},
            'ip_address': None,
            'email': None
        }
        assert event['request'] == {
            'env': {'SERVER_NAME': 'localhost', 'SERVER_PORT': '80'},
            'cookies': {},
            'headers': {'Host': 'localhost:80'},
            'method': 'GET',
            'query_string': '',
            'url': 'http://localhost/test',
        }
    else:
        assert event['user'] == {'id': None, 'data': {'role': 'anonymous'}}
        assert event['request'] == {
            'env': {'SERVER_NAME': 'localhost', 'SERVER_PORT': '80'},
            'headers': {'Host': 'localhost:80'},
            'method': 'GET',
            'query_string': '',
            'url': 'http://localhost/test',
        }
    assert event['transaction'] == '/test'

    extra = event['extra']
    assert extra['namespace'] == sentry_app.namespace
    assert extra['application_id'] == sentry_app.application_id


@pytest.mark.parametrize('sentry_app', [
    pytest.param(True, id='with ppi'),
    pytest.param(False, id='without ppi'),
], indirect=['sentry_app'])
def test_has_context_logged_in(
    mock_view: Mock,
    sentry_app: Framework,
    sentry_client: Client,
    capture_events: Callable[[], list[Event]]
) -> None:

    events = capture_events()

    def view(self: object, request: CoreRequest) -> Response:
        # we patch the user information into the request, so we don't
        # have to implement a user login to test this
        request.environ['HTTP_X_REAL_IP'] = '1.2.3.4'
        request.identity = Identity(
            userid='test@example.org',
            uid='1',
            role='admin',
            groupids=frozenset(),
            application_id=sentry_app.application_id
        )
        capture_message('test_message')
        return Response()

    mock_view.side_effect = view

    sentry_client.get('/test')

    (event,) = events
    user = event['user']
    assert user['id'] == '1'
    assert user['data']['role'] == 'admin'  # type: ignore[index]
    if sentry_app.with_ppi:  # type: ignore[attr-defined]
        assert user['email'] == 'test@example.org'
        assert user['ip_address'] == '1.2.3.4'
    else:
        assert 'test@example.org' not in user.values()
