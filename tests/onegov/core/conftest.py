from __future__ import annotations

import os.path
import pytest
import transaction
import yaml

from tests.shared import Client
from tests.shared.utils import create_app
from onegov.core.cli import command_group
from onegov.core.elements import Element
from onegov.core.framework import Framework
from onegov.core.layout import ChameleonLayout


from typing import cast, TYPE_CHECKING
if TYPE_CHECKING:
    from click import Group
    from collections.abc import Callable
    from onegov.core.request import CoreRequest
    from pytest_localserver.smtp import Server as SmtpServer  # type: ignore[import-untyped]
    from typing import type_check_only
    from webtest import TestResponse

    @type_check_only
    class TestGroup(Group):
        called: bool
        called_request: bool

    @type_check_only
    class SmtpApp(Framework):
        smtp: SmtpServer


@pytest.fixture(scope='session', autouse=True)
def cache_password_hashing(monkeysession: pytest.MonkeyPatch) -> None:
    pass  # override the password hashing set by tests.shared for the core


@pytest.fixture(scope='function')
def cli(request: pytest.FixtureRequest) -> TestGroup:
    cli = cast('TestGroup', command_group())

    @cli.command(context_settings=request.param or {})
    def create() -> Callable[[CoreRequest, Framework], None]:
        nonlocal cli
        cli.called = True

        def perform(request: CoreRequest, app: Framework) -> None:
            cli.called_request = True

        return perform

    return cli


@pytest.fixture(scope='function')
def cli_config(
    postgres_dsn: str,
    redis_url: str,
    temporary_directory: str
) -> str:

    cfg = {
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': {
                    'dsn': postgres_dsn,
                    'redis_url': redis_url,
                }
            }
        ]
    }

    path = os.path.join(temporary_directory, 'onegov.yml')

    with open(path, 'w') as f:
        f.write(yaml.dump(cfg))

    return path


@pytest.fixture(scope='function')
def render_element(
    request: pytest.FixtureRequest
) -> Callable[[Element], TestResponse]:

    class App(Framework):
        element: Element

    @App.path(path='/element', model=Element)
    def get_element(app: App) -> Element:
        return app.element

    @App.html(model=Element)
    def render_element(self: Element, request: CoreRequest) -> str:
        return self(ChameleonLayout(getattr(self, 'model', None), request))

    app = create_app(App, request, enable_search=False)
    transaction.commit()

    client = Client(app)

    def render(element: Element) -> TestResponse:
        app.element = element
        return client.get('/element')

    return render


@pytest.fixture(scope='function')
def maildir_app(temporary_directory: str, maildir: str) -> Framework:
    postmark_cfg = {
        'mailer': 'postmark',
        'directory': maildir,
        'token': 'token'
    }
    app_cfg = {
        'mail': {
            'marketing': {
                **postmark_cfg,
                'sender': 'noreply@example.org'
            },
            'transactional': {
                **postmark_cfg,
                'sender': 'noreply@example.org'
            }
        }
    }

    cfg = {
        'mail_queues': {
            'postmark': postmark_cfg
        },
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': app_cfg
            }
        ]
    }

    with open(os.path.join(temporary_directory, 'onegov.yml'), 'w') as f:
        f.write(yaml.dump(cfg))

    app = Framework()
    app.namespace = 'test'
    app.configure_application(**app_cfg)

    return app


@pytest.fixture(scope='function')
def maildir_smtp_app(
    temporary_directory: str,
    maildir: str,
    smtp: SmtpServer
) -> SmtpApp:

    smtp_cfg = {
        'mailer': 'smtp',
        'directory': maildir,
        'host': smtp.addr[0],
        'port': smtp.addr[1],
        'force_tls': False,
        'username': None,
        'password': None,
    }

    app_cfg = {
        'mail': {
            'marketing': {
                **smtp_cfg,
                'sender': 'noreply@example.org'
            },
            'transactional': {
                **smtp_cfg,
                'sender': 'noreply@example.org'
            }
        }
    }

    cfg = {
        'mail_queues': {
            'smtp': smtp_cfg
        },
        'applications': [
            {
                'path': '/foobar/*',
                'application': 'onegov.core.Framework',
                'namespace': 'foobar',
                'configuration': app_cfg
            }
        ]
    }

    with open(os.path.join(temporary_directory, 'onegov.yml'), 'w') as f:
        f.write(yaml.dump(cfg))

    app = cast('SmtpApp', Framework())
    app.namespace = 'test'
    app.configure_application(**app_cfg)
    app.smtp = smtp

    return app
