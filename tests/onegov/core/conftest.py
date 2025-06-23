import os.path
import pytest
import transaction
import yaml

from tests.onegov.org.conftest import create_org_app
from tests.shared import Client
from tests.shared.utils import create_app
from onegov.core.cli import command_group
from onegov.core.elements import Element
from onegov.core.framework import Framework
from onegov.core.layout import ChameleonLayout


@pytest.fixture(scope='session', autouse=True)
def cache_password_hashing(monkeysession):
    pass  # override the password hashing set by tests.shared for the core


@pytest.fixture(scope='function')
def cli(request):
    cli = command_group()

    @cli.command(context_settings=request.param or {})
    def create():
        nonlocal cli
        cli.called = True

        def perform(request, app):
            cli.called_request = True

        return perform

    return cli


@pytest.fixture(scope='function')
def cli_config(postgres_dsn, redis_url, temporary_directory):
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
def render_element(request):
    class App(Framework):
        pass

    @App.path(path='/element', model=Element)
    def get_element(app):
        return app.element

    @App.html(model=Element)
    def render_element(self, request):
        return self(ChameleonLayout(getattr(self, 'model', None), request))

    app = create_app(App, request, use_elasticsearch=False)
    transaction.commit()

    client = Client(app)

    def render(element):
        app.element = element
        return client.get('/element')

    return render


@pytest.fixture(scope='function')
def maildir_app(temporary_directory, maildir):
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
def maildir_smtp_app(temporary_directory, maildir, smtp):
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

    app = Framework()
    app.namespace = 'test'
    app.configure_application(**app_cfg)
    app.smtp = smtp

    return app


@pytest.fixture(scope='function')
def org_app(request):
    yield create_org_app(request, use_elasticsearch=False)


@pytest.fixture(scope='function')
def core_request(org_app):
    yield org_app.request_class(environ={
        'PATH_INFO': '/',
        'SERVER_NAME': '',
        'SERVER_PORT': '',
        'SERVER_PROTOCOL': 'https'
    }, app=org_app)
